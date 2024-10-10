import os
from flask import Flask, render_template, request, redirect, url_for, session
import logging
from requests_oauthlib import OAuth2Session
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Allow OAuth over HTTP (for development only)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Add this line to set a secret key for sessions
logging.basicConfig(level=logging.DEBUG)

# Basecamp credentials
account_id = os.getenv('BASECAMP_ACCOUNT_ID')
client_id = os.getenv('BASECAMP_CLIENT_ID')
client_secret = os.getenv('BASECAMP_CLIENT_SECRET')
redirect_uri = 'http://localhost:8001/oauth/callback'

logging.debug(f"BASECAMP_ACCOUNT_ID: {account_id}")
logging.debug(f"BASECAMP_CLIENT_ID: {client_id}")
logging.debug(f"BASECAMP_CLIENT_SECRET: {client_secret[:5]}...") # Only log the first 5 characters of the secret

# OAuth endpoints
authorization_base_url = "https://launchpad.37signals.com/authorization/new"
token_url = "https://launchpad.37signals.com/authorization/token"

def get_projects(token):
    logging.debug(f"Attempting to fetch Basecamp projects for account {account_id}")
    try:
        oauth = OAuth2Session(client_id, token=token)
        url = f'https://3.basecampapi.com/{account_id}/projects.json'
        all_projects = []
        
        while url:
            response = oauth.get(url)
            logging.debug(f"Basecamp API response status: {response.status_code}")
            
            if response.status_code == 200:
                projects = response.json()
                all_projects.extend(projects)
                
                # Check for next page
                link_header = response.headers.get('Link', '')
                if 'rel="next"' in link_header:
                    url = link_header.split(';')[0].strip('<>')
                else:
                    url = None
            else:
                logging.error(f"Failed to fetch projects: {response.text}")
                return None
        
        return all_projects
    except Exception as e:
        logging.exception(f"An error occurred while fetching projects: {str(e)}")
        return None

@app.route('/')
def index():
    logging.debug("Index route accessed")
    oauth = OAuth2Session(client_id, redirect_uri=redirect_uri)
    authorization_url, state = oauth.authorization_url(
        authorization_base_url,
        type='web_server'
    )
    session['oauth_state'] = state
    return redirect(authorization_url)

@app.route('/oauth/callback')
def callback():
    logging.debug("Callback route accessed")
    oauth = OAuth2Session(client_id, state=session['oauth_state'], redirect_uri=redirect_uri)
    token = oauth.fetch_token(
        token_url,
        client_secret=client_secret,
        authorization_response=request.url,
        include_client_id=True,
        type='web_server'
    )
    logging.debug(f"Token received: {token}")
    projects = get_projects(token)
    if projects:
        return render_template('projects.html', projects=projects)
    else:
        return "Failed to retrieve projects", 500

@app.route('/test')
def test():
    logging.debug("Test route accessed")
    return "Flask app is running", 200

@app.route('/hello')
def hello():
    return "Hello, World!"

if __name__ == '__main__':
    print("Starting Flask app on http://0.0.0.0:8001")
    app.run(host='0.0.0.0', port=8001, debug=True)