from flask import Flask, redirect, request, url_for, jsonify, make_response, abort, session
from flask_cors import CORS
import json
import requests
import time
import os
import datetime

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
   if session and "access_token" not in session and not ("login" in request.endpoint or "authorize" in request.endpoint or "user" in request.endpoint):
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

if __name__ == "__main__":
   # localhost or server?
   if cfg['server']:
      app.run(host='0.0.0.0')
   else:
    app.run()