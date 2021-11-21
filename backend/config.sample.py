config = {
    'sql': {
        'user': '',
        'password': '',
        'host': 'localhost',
        'port': 3306,
        'database': 'groupme_reminder_bot',
    },
    'server': False, # False if running on localhost, True running with uWSGI / NGINX
    'sql_logging': False,
    'groupme_redirect_url': '', # redirect URL of GroupMe Application
    'frontend_url': ''
}