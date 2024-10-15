from flask import Flask, jsonify, request, render_template, send_file
from requests_oauthlib import OAuth2Session
import os
import logging
import requests
import pprint
from logging.config import dictConfig
from werkzeug.utils import secure_filename

app = Flask(__name__)
dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'DEBUG',
        'handlers': ['wsgi']
    }
})

# Add these lines near the top of your file, after the imports
BASECAMP_ACCOUNT_ID = os.environ.get('BASECAMP_ACCOUNT_ID')
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
REDIRECT_URI = os.environ.get('REDIRECT_URI')

oauth = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI)

@app.before_request
def log_request_info():
    app.logger.debug('Headers: %s', request.headers)
    app.logger.debug('Body: %s', request.get_data())

@app.after_request
def log_response_info(response):
    app.logger.debug('Response Status: %s', response.status)
    app.logger.debug('Response Headers: %s', response.headers)
    return response

@app.route('/todos/<int:project_id>/<int:todolist_id>')
def get_todos(project_id, todolist_id):
    app.logger.debug(f"Received request for todos with project_id: {project_id} and todolist_id: {todolist_id}")
    
    access_token = get_access_token()
    
    url = f"https://3.basecampapi.com/{BASECAMP_ACCOUNT_ID}/buckets/{project_id}/todolists/{todolist_id}/todos.json"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        todos = response.json()
        
        app.logger.debug("Received todos:")
        app.logger.debug(pprint.pformat(todos, width=160, compact=False))
        
        # Remove the detailed_todos fetching for now to simplify the response
        
        app.logger.info("Returning todos:")
        app.logger.info(pprint.pformat(todos, width=160, compact=False))
        
        return jsonify(todos), 200
    except requests.RequestException as e:
        app.logger.error(f"Error fetching todos: {str(e)}")
        return jsonify({"error": str(e)}), 500

def get_access_token():
    return "your_access_token_here"  # Replace with your actual access token

@app.errorhandler(404)
def not_found_error(error):
    app.logger.error(f"404 error: {str(error)}")
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"500 error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500

@app.route('/todos')
def todos_page():
    return render_template('todos.html', BASECAMP_ACCOUNT_ID=BASECAMP_ACCOUNT_ID)

@app.route('/test')
def test():
    return jsonify({"message": "Test route working"}), 200

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    print(f"Caught request for path: {path}")
    return jsonify({"error": f"Path not found: {path}"}), 404

# Add this new route for file upload
@app.route('/upload_attachment/<int:project_id>', methods=['POST'])
def upload_attachment(project_id):
    access_token = get_access_token()
    
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file:
        filename = secure_filename(file.filename)
        upload_url = f"https://3.basecampapi.com/{BASECAMP_ACCOUNT_ID}/buckets/{project_id}/attachments.json"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': file.content_type
        }
        
        try:
            response = requests.post(upload_url, headers=headers, data=file)
            response.raise_for_status()
            attachment_data = response.json()
            
            # Return the URL of the uploaded attachment
            return jsonify({"url": attachment_data['url']}), 200
        except requests.RequestException as e:
            app.logger.error(f"Error uploading attachment: {str(e)}")
            return jsonify({"error": str(e)}), 500

# Modify the existing create_todo function or add a new one if it doesn't exist
@app.route('/create_todo/<int:project_id>/<int:todolist_id>', methods=['POST'])
def create_todo(project_id, todolist_id):
    access_token = get_access_token()
    
    data = request.json
    title = data.get('title')
    notes = data.get('notes')
    
    if not title:
        return jsonify({"error": "Title is required"}), 400
    
    url = f"https://3.basecampapi.com/{BASECAMP_ACCOUNT_ID}/buckets/{project_id}/todolists/{todolist_id}/todos.json"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    todo_data = {
        "content": title,
        "description": notes
    }
    
    try:
        response = requests.post(url, headers=headers, json=todo_data)
        response.raise_for_status()
        new_todo = response.json()
        return jsonify(new_todo), 201
    except requests.RequestException as e:
        app.logger.error(f"Error creating todo: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting Flask app...")
    app.run(debug=True, host='0.0.0.0', port=8001)
