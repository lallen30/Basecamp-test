import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
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
        
        logging.debug(f"Fetched {len(all_projects)} projects")
        logging.debug(f"Project IDs: {[project['id'] for project in all_projects]}")
        return all_projects
    except Exception as e:
        logging.exception(f"An error occurred while fetching projects: {str(e)}")
        return None

def get_todo_lists(token, project_id):
    logging.debug(f"Attempting to fetch todo lists for project {project_id}")
    try:
        oauth = OAuth2Session(client_id, token=token)
        headers = {
            'User-Agent': 'YourAppName (yourname@example.com)'
        }

        # First, fetch the project details
        project_url = f'https://3.basecampapi.com/{account_id}/projects/{project_id}.json'
        project_response = oauth.get(project_url, headers=headers)
        
        logging.debug(f"Project API response status: {project_response.status_code}")
        logging.debug(f"Project API response content: {project_response.text[:1000]}...")  # Log first 1000 characters
        
        if project_response.status_code != 200:
            logging.error(f"Failed to fetch project details: {project_response.text}")
            return None

        project_data = project_response.json()
        
        # Find the todoset in the project details
        todoset = next((dock for dock in project_data.get('dock', []) if dock['name'] == 'todoset'), None)
        
        if not todoset:
            logging.error("Todoset not found in project details")
            return None

        # Now fetch the todoset details
        todoset_response = oauth.get(todoset['url'], headers=headers)
        
        logging.debug(f"Todo lists API response status: {todoset_response.status_code}")
        logging.debug(f"Todo lists API response headers: {todoset_response.headers}")
        logging.debug(f"Todo lists API response content: {todoset_response.text[:1000]}...")  # Log first 1000 characters
        
        if todoset_response.status_code == 200:
            todoset_data = todoset_response.json()
            # The actual todo lists are not in this response, we need to fetch them separately
            todo_lists_url = todoset_data.get('todolists_url')
            if todo_lists_url:
                todo_lists_response = oauth.get(todo_lists_url, headers=headers)
                if todo_lists_response.status_code == 200:
                    todo_lists = todo_lists_response.json()
                    return [{'id': list['id'], 'name': list['name']} for list in todo_lists]
                else:
                    logging.error(f"Failed to fetch todo lists: {todo_lists_response.text}")
                    return None
            else:
                logging.error("Todo lists URL not found in todoset data")
                return None
        else:
            logging.error(f"Failed to fetch todoset: {todoset_response.text}")
            return None
    except Exception as e:
        logging.exception(f"An error occurred while fetching todo lists: {str(e)}")
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
    session['oauth_token'] = token
    projects = get_projects(token)
    if projects:
        return render_template('projects.html', projects=projects)
    else:
        return "Failed to retrieve projects", 500

@app.route('/todo_lists/<project_id>')
def todo_lists(project_id):
    token = session.get('oauth_token')
    if not token:
        logging.error("No OAuth token found in session")
        return jsonify({"error": "No OAuth token found. Please re-authenticate."}), 401
    
    todo_lists = get_todo_lists(token, project_id)
    if todo_lists is None:
        return jsonify({"error": "Failed to fetch todo lists. The project might not exist, you might not have access to it, or there was an API error. Please check the server logs for more details."}), 500
    return jsonify(todo_lists)

@app.route('/test')
def test():
    logging.debug("Test route accessed")
    return "Flask app is running", 200

@app.route('/hello')
def hello():
    return "Hello, World!"

# Add this new import at the top of the file
from flask import request

# Add this new function to create a todo
def create_todo(token, project_id, todolist_id, title, notes):
    logging.debug(f"Attempting to create a new todo in project {project_id}, todolist {todolist_id}")
    try:
        oauth = OAuth2Session(client_id, token=token)
        headers = {
            'User-Agent': 'YourAppName (yourname@example.com)',
            'Content-Type': 'application/json'
        }
        url = f'https://3.basecampapi.com/{account_id}/buckets/{project_id}/todolists/{todolist_id}/todos.json'
        data = {
            'content': title,
            'description': notes
        }
        response = oauth.post(url, headers=headers, json=data)
        
        logging.debug(f"Create todo API response status: {response.status_code}")
        logging.debug(f"Create todo API response content: {response.text[:1000]}...")  # Log first 1000 characters
        
        if response.status_code == 201:
            return response.json()
        else:
            logging.error(f"Failed to create todo: {response.text}")
            return None
    except Exception as e:
        logging.exception(f"An error occurred while creating todo: {str(e)}")
        return None

# Add this new route to handle the form submission
@app.route('/create_todo', methods=['POST'])
def handle_create_todo():
    token = session.get('oauth_token')
    if not token:
        logging.error("No OAuth token found in session")
        return jsonify({"error": "No OAuth token found. Please re-authenticate."}), 401
    
    data = request.json
    project_id = data.get('projectId')
    todolist_id = data.get('todoListId')
    title = data.get('title')
    notes = data.get('notes')
    
    if not project_id or not todolist_id or not title:
        return jsonify({"error": "Missing required fields"}), 400
    
    result = create_todo(token, project_id, todolist_id, title, notes)
    if result:
        return jsonify({"message": "Todo created successfully", "todo": result}), 201
    else:
        return jsonify({"error": "Failed to create todo. Please check the server logs for more details."}), 500

if __name__ == '__main__':
    print("Starting Flask app on http://0.0.0.0:8001")
    app.run(host='0.0.0.0', port=8001, debug=True)