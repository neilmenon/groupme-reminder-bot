from flask import Flask, redirect, request, url_for, jsonify, make_response, abort, session
from flask_cors import CORS
import json
import requests
import time
import os
import datetime
import random

import config
import sql_helper
import api_logger as logger

cfg = config.config

app = Flask(__name__)
app.config["DEBUG"] = True
app.secret_key = os.urandom(36)
CORS(app)

@app.before_request
def before_request():
   if session and "access_token" not in session and not ("login" in request.endpoint or "authorize" in request.endpoint or "user" in request.endpoint or "reminder-task" in request.endpoint):
      session['login_redirect'] = request.url
      return redirect("/api/login")

@app.route('/api', methods=['GET'])
def index():
   return jsonify({'data': 'success'})

@app.route('/api/user', methods=['GET'])
def users(): # gets the currently logged in user if logged in, else returns blank object
   if session and "access_token" in session:
      user = sql_helper.execute_db("SELECT id,name,num_reminders,image_url,access_token FROM users WHERE id = {}".format(session['user_id']))[0]
      user['bot_groups'] = [u['group_id'] for u in sql_helper.execute_db("SELECT group_id FROM part_of WHERE user_id = {}".format(user['id']))]
      return jsonify(user)
   else:
      return jsonify(None)

@app.route('/api/login', methods=['GET'])
def login():
   return redirect(cfg['groupme_redirect_url'])

@app.route('/api/logout', methods=['GET'])
def logout():
   del session['access_token']
   del session['user_id']
   return redirect(cfg['frontend_url'])

@app.route('/api/authorize', methods=['GET'])
def authorize():
   access_token = request.args.get("access_token")
   if not access_token:
      abort(400)

   # check if we can user by access_token
   result = sql_helper.execute_db("SELECT id FROM users WHERE access_token = '{}'".format(access_token))
   if len(result):
      # nothing to do!
      data = result[0]
   else:
      # get user from GroupMe API
      user = requests.get("https://api.groupme.com/v3/users/me?access_token={}".format(access_token)).json()
      data: dict = {
         "id": user['response']['id'],
         "name": user['response']['name'],
         "image_url": user['response']['image_url'],
         "access_token": access_token,
         "num_reminders": 0
      }

      # if they already exist in DB but have different access token, update access token
      result = sql_helper.execute_db("SELECT access_token FROM users WHERE id = {}".format(data['id']))
      if len(result):
         if result[0]['access_token'] != access_token: # update the access token
            sql_helper.execute_db("UPDATE users SET access_token = '{}' WHERE id = {}".format(access_token, data['id']), commit=True)
      else:
         # insert user into database if they don't already exist
         sql_helper.execute_db(sql_helper.insert_into_where_not_exists("users", data, "id"), commit=True)

   session['access_token'] = access_token
   session['user_id'] = data['id']

   if "login_redirect" in session: # redirect to previous request after successful login
      login_redirect = session['login_redirect']
      del session['login_redirect']
      return redirect(login_redirect)
   else: # redirect to frontend
      return redirect(cfg['frontend_url'])

@app.route('/api/register-bot', methods=['POST'])
def add_bot():
   params = request.get_json()
   if params:
      try:
         group_id = params['group_id']
      except KeyError as e:
         response = make_response(jsonify(error="Missing required parameter: " + str(e.args[0]) + "."), 400)
         abort(response)
   
   # create bot 
   data = {}
   data['bot'] = {
      "name": "Reminder Bot",
      "group_id": str(group_id),
      "avatar_url": "https://i.imgur.com/Lqr2s5N.png",
      "callback_url": cfg['callback_url'] + group_id
   }
   logger.log(data)
   resp = requests.post("https://api.groupme.com/v3/bots?token={}".format(session['access_token']), json=data).json()

   # create entry in groups table
   data = {
      "id": group_id,
      "name": resp['response']['bot']['group_name'],
      "added_bot_date": str(datetime.datetime.now()),
      "bot_id": resp['response']['bot']['bot_id']
   }
   sql_helper.execute_db(sql_helper.insert_into_where_not_exists("groups", data, "id"), commit=True)

   # create association in part_of table
   data = { "user_id": session['user_id'], "group_id": group_id }
   sql_helper.execute_db(sql_helper.insert_into("part_of", data), commit=True)

   # create bot setting entry
   setting_id = random.randint(1,5000)
   sql_helper.execute_db(sql_helper.insert_into("bot_setting", { "id": setting_id, "settings_json": '{ "prefix": "❗❗❗REMINDER: " }' }), commit=True)

   # create has_setting association
   sql_helper.execute_db(sql_helper.insert_into("has_setting", { "group_id": group_id, "setting_id": setting_id }), commit=True)

   # send welcome message
   data = { "text": "Thanks for adding Reminder Bot to your group! If you are a group admin, you can manage me by visiting the dashboard at {}. Happy reminding!".format(cfg['frontend_url']), "bot_id": resp['response']['bot']['bot_id'] }
   resp = requests.post("https://api.groupme.com/v3/bots/post", json=data)

   return jsonify(True)

@app.route('/api/groups/<int:group_id>/delete', methods=['DELETE'])
def delete_group(group_id):
   # get group
   group = sql_helper.execute_db("SELECT * FROM groups WHERE id = {}".format(group_id))[0]

   # destroy bot from group
   requests.post("https://api.groupme.com/v3/bots/destroy?token={}".format(session['access_token']), json={"bot_id": group['bot_id']})

   # remove associations from part_of table
   sql_helper.execute_db("DELETE FROM part_of WHERE group_id = {}".format(group_id), commit=True)

   # delete group
   sql_helper.execute_db("DELETE FROM groups WHERE id = {}".format(group_id), commit=True)

   return jsonify(True)

@app.route('/api/groups/<int:group_id>', methods=['GET'])
def get_group(group_id):
   result = sql_helper.execute_db("SELECT id FROM groups WHERE id = {}".format(group_id))
   return jsonify(result[0]) if len(result) else jsonify(None)

@app.route('/api/reminders/create', methods=['POST'])
def create_reminder():
   params = request.get_json()
   if params:
      try:
         group_id = params['group_id']
         text = params['text']
         timestamp = params['timestamp']
         frequency = params['frequency']
      except KeyError as e:
         response = make_response(jsonify(error="Missing required parameter: " + str(e.args[0]) + "."), 400)
         abort(response)

   data: dict = {
      "id": random.randint(0, 5000),
      "text": text,
      "timestamp": timestamp,
   }
   if frequency:
      data['frequency'] = frequency

   # insert reminder into table
   sql_helper.execute_db(sql_helper.insert_into("reminder", data), commit=True)

   # insert creates relation
   sql_helper.execute_db(sql_helper.insert_into("creates", { "user_id": session['user_id'], "reminder_id": data['id'] }), commit=True)

   # insert reminds relation
   sql_helper.execute_db(sql_helper.insert_into("reminds", { "group_id": group_id, "reminder_id": data['id'] }), commit=True)

   # return list of group's reminders
   return jsonify(sql_helper.execute_db("SELECT reminder.*, reminds.group_id FROM reminder NATURAL JOIN reminds WHERE reminder.id = reminds.reminder_id AND reminds.group_id = {}".format(group_id)))

@app.route('/api/reminders/get', methods=['POST'])
def get_reminder():
   params = request.get_json()
   if params:
      try:
         group_id = params['group_id']
         sort_by = params['sort_by']
         sort_order = params['sort_order']
      except KeyError as e:
         response = make_response(jsonify(error="Missing required parameter: " + str(e.args[0]) + "."), 400)
         abort(response)

   # return list of group's reminders
   return jsonify(sql_helper.execute_db("SELECT reminder.* FROM reminder NATURAL JOIN reminds WHERE reminder.id = reminds.reminder_id AND reminds.group_id = {} ORDER BY {} {}".format(group_id, sort_by, sort_order)))

@app.route('/api/reminders/delete', methods=['POST'])
def delete_reminder():
   params = request.get_json()
   if params:
      try:
         reminder_id = params['reminder_id']
         group_id = params['group_id']
      except KeyError as e:
         response = make_response(jsonify(error="Missing required parameter: " + str(e.args[0]) + "."), 400)
         abort(response)

   # delete reminder
   sql_helper.execute_db("DELETE FROM reminder WHERE id = {}".format(reminder_id), commit=True)
   
   # return reminders
   return jsonify(sql_helper.execute_db("SELECT reminder.*, reminds.group_id FROM reminder NATURAL JOIN reminds WHERE reminder.id = reminds.reminder_id AND reminds.group_id = {}".format(group_id)))

@app.route('/api/reminders/reminder-task', methods=['POST'])
def reminder_task():
   time.sleep(2)
   params = request.get_json()
   if params:
      try:
         sk = params['secret_key']
      except KeyError as e:
         response = make_response(jsonify(error="Missing required parameter: " + str(e.args[0]) + "."), 400)
         abort(response)

   if sk != cfg['secret_key']:
      abort(401)

   # get all reminders
   result = sql_helper.execute_db("SELECT reminder.*, reminds.group_id, bot_setting.settings_json, groups.bot_id FROM reminder LEFT JOIN reminds ON reminder.id = reminds.reminder_id LEFT JOIN groups ON groups.id = reminds.group_id LEFT JOIN has_setting ON has_setting.group_id = reminds.group_id LEFT JOIN bot_setting ON bot_setting.id = has_setting.setting_id")
   for reminder in result:
      reminder_date = datetime.datetime.utcfromtimestamp(int(reminder['timestamp']))
      if reminder_date < datetime.datetime.utcnow(): # needs to be sent!
         logger.log("Sending reminder: {}".format(reminder))

         settings_json = json.loads(reminder['settings_json'])

         # create  & send reminder
         data = { "text": "{}{}".format(settings_json['prefix'], reminder['text']), "bot_id": reminder['bot_id'] }
         requests.post("https://api.groupme.com/v3/bots/post", json=data)

         # create entry in reminder history:
         data = {
            "reminder_id": reminder['id'],
            "sent": str(int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())),
            "text": reminder['text'],
            "group_id": reminder['group_id']
         }
         sql_helper.execute_db(sql_helper.insert_into("reminder_history", data), commit=True)

         if reminder['frequency']: # set new date to send
            new_date = int(reminder['timestamp']) + 60 * reminder['frequency']
            sql_helper.execute_db("UPDATE reminder SET timestamp = '{}' WHERE id = {}".format(new_date, reminder['id']), commit=True)
         else: # delete reminder from DB
            sql_helper.execute_db("DELETE FROM reminder WHERE id = {}".format(reminder['id']), commit=True)

   # return reminders
   return jsonify(True)

@app.route('/api/groups/<int:group_id>/reminder-history', methods=['GET'])
def reminder_history(group_id):
   return jsonify(sql_helper.execute_db("SELECT * FROM reminder_history WHERE group_id = {} ORDER BY sent DESC".format(group_id)))

@app.route('/api/groups/<int:group_id>/settings', methods=['GET'])
def bot_settings_get(group_id):
   result = sql_helper.execute_db("SELECT bot_setting.* FROM bot_setting NATURAL JOIN has_setting WHERE has_setting.group_id = {}".format(group_id))[0]
   result['settings_json'] = json.loads(result['settings_json'])
   return jsonify(result)

@app.route('/api/groups/<int:group_id>/settings', methods=['POST'])
def bot_settings_update(group_id):
   params = request.get_json()
   setting_id = params['id']
   del params['id']
   json_str = '{"prefix": "' + params['prefix'] + '"}'
   sql_helper.execute_db("UPDATE bot_setting SET settings_json = '{}' WHERE id = {}".format(json_str, setting_id), commit=True)
   return jsonify(True)

@app.route('/api/groups/<int:group_id>/keyword-mapping', methods=['GET'])
def keyword_get(group_id):
   return jsonify(sql_helper.execute_db("SELECT phrase, mapping FROM keyword_mapping WHERE group_id = {}".format(group_id)))

@app.route('/api/groups/<int:group_id>/keyword-mapping', methods=['POST'])
def keyword_post(group_id):
   params = request.get_json()
   if params:
      try:
         phrase = params['phrase']
         mapping = params['mapping']
      except KeyError as e:
         response = make_response(jsonify(error="Missing required parameter: " + str(e.args[0]) + "."), 400)
         abort(response)

   if phrase.lower() in mapping.lower():
      response = make_response(jsonify(error="Phrase cannot be in mapping."), 400)
      abort(response)

   data = {
      "group_id": group_id,
      "phrase": phrase,
      "mapping": mapping
   }
   sql_helper.execute_db(sql_helper.replace_into("keyword_mapping", data), commit=True)
   return jsonify(sql_helper.execute_db("SELECT phrase, mapping FROM keyword_mapping WHERE group_id = {}".format(group_id)))

@app.route('/api/groups/<int:group_id>/keyword-mapping/delete', methods=['POST'])
def keyword_del(group_id):
   params = request.get_json()
   if params:
      try:
         phrase = params['phrase']
         mapping = params['mapping']
      except KeyError as e:
         response = make_response(jsonify(error="Missing required parameter: " + str(e.args[0]) + "."), 400)
         abort(response)

   sql_helper.execute_db("DELETE FROM keyword_mapping WHERE phrase = '{}' AND mapping = '{}' AND group_id = {}".format(phrase, mapping, group_id), commit=True)
   return jsonify(sql_helper.execute_db("SELECT phrase, mapping FROM keyword_mapping WHERE group_id = {}".format(group_id)))

@app.route('/api/msg-callback/<int:group_id>', methods=['POST'])
def msg_callback(group_id):
   params = request.get_json()
   message: str = params['text']
   logger.log(params)

   # check if message text includes any keyword mappings
   result = sql_helper.execute_db("SELECT phrase,mapping FROM keyword_mapping WHERE group_id = {}".format(group_id))

   for m in result:
      if m['phrase'].lower() in message.lower() and m['mapping'].lower() != message.lower():
         # match! send mapping...
         bot_id = sql_helper.execute_db("SELECT bot_id FROM groups WHERE id = {}".format(group_id))[0]['bot_id']
         
         data = { "text": m['mapping'], "bot_id": bot_id }
         requests.post("https://api.groupme.com/v3/bots/post", json=data)

   return jsonify(True)

if __name__ == "__main__":
   # localhost or server?
   if cfg['server']:
      app.run(host='0.0.0.0')
   else:
    app.run()