from flask import Flask, render_template, request, jsonify, send_from_directory, session
import os
import time
import uuid
import threading
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from utils.colorize import colorize_image

app = Flask(__name__)
app.secret_key = 'your_secure_random_key_here'  # Required for sessions

# Configuration
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.config['FILE_RETENTION_MINUTES'] = 60  # How long to keep files

# Database to store file metadata (using a simple file in this example)
# In production, use a real database instead
FILE_DB_PATH = 'file_metadata.json'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_file_db():
    """Load the file database or create if not exists"""
    if os.path.exists(FILE_DB_PATH):
        try:
            with open(FILE_DB_PATH, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {'files': []}
    else:
        return {'files': []}

def save_file_db(db):
    """Save the file database"""
    with open(FILE_DB_PATH, 'w') as f:
        json.dump(db, f)

def register_file(file_path, session_id):
    """Register a file in the database with creation time and session"""
    db = get_file_db()
    db['files'].append({
        'path': file_path,
        'created': time.time(),
        'session_id': session_id
    })
    save_file_db(db)

def scheduled_cleanup():
    """Background task to clean up expired files"""
    while True:
        try:
            cleanup_files()
        except Exception as e:
            print(f"Error in scheduled cleanup: {e}")
        # Sleep for 15 minutes before next cleanup
        time.sleep(15 * 60)

def cleanup_files():
    """Remove files that are older than the retention period"""
    db = get_file_db()
    current_time = time.time()
    retention_seconds = app.config['FILE_RETENTION_MINUTES'] * 60
    
    # Track which files to remove from the database
    files_to_remove = []
    
    for file_entry in db['files']:
        # Check if file is older than retention period
        if current_time - file_entry['created'] > retention_seconds:
            file_path = file_entry['path']
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"Removed expired file: {file_path}")
                except Exception as e:
                    print(f"Error removing {file_path}: {e}")
            # Mark this entry for removal from the database
            files_to_remove.append(file_entry)
    
    # Remove expired entries from the database
    if files_to_remove:
        db['files'] = [f for f in db['files'] if f not in files_to_remove]
        save_file_db(db)
        print(f"Cleaned up {len(files_to_remove)} file records")

@app.route('/')
def index():
    # Create a session ID if not exists
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return render_template('index.html')

@app.route('/api/colorize', methods=['POST'])
def api_colorize():
    # Get or create session ID
    session_id = session.get('session_id', str(uuid.uuid4()))
    session['session_id'] = session_id
    
    # Check if image is in the request
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    file = request.files['image']
    
    # Check if file is empty
    if file.filename == '':
        return jsonify({'error': 'No image selected'}), 400
    
    # Check if file is allowed
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    # Generate a unique filename for both original and colorized images
    unique_id = str(uuid.uuid4())
    filename = secure_filename(file.filename)
    base, ext = os.path.splitext(filename)
    
    original_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_original{ext}")
    colorized_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_colorized{ext}")
    
    # Save the original image
    file.save(original_path)
    
    # Register files in the database
    register_file(original_path, session_id)
    
    try:
        # Process the image (colorize it)
        colorize_image(original_path, colorized_path)
        
        # Register the colorized file too
        register_file(colorized_path, session_id)
        
        # Return paths to both images
        return jsonify({
            'original': f"/static/uploads/{os.path.basename(original_path)}",
            'colorized': f"/static/uploads/{os.path.basename(colorized_path)}",
            'session_id': session_id  # Return session ID to client
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/placeholder/<width>/<height>')
def placeholder(width, height):
    """Simple placeholder route to simulate the video source in the template"""
    return send_from_directory('static', 'placeholder.mp4')

@app.after_request
def add_header(response):
    """Add headers to disable caching for development purposes"""
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

# Route to clean up specific files
@app.route('/api/cleanup', methods=['POST'])
def cleanup_specific():
    """Endpoint to clean up specific files"""
    data = request.json
    session_id = session.get('session_id', '')
    
    if 'files' in data and isinstance(data['files'], list):
        db = get_file_db()
        files_to_remove = []
        
        for file_path in data['files']:
            # Make sure to convert to absolute path
            if file_path.startswith('/'):
                absolute_path = os.path.join(app.root_path, file_path[1:])
            else:
                absolute_path = os.path.join(app.root_path, file_path)
            
            # Find the corresponding entry in the database
            for file_entry in db['files']:
                # Only allow deletion of files from the same session
                if (file_entry['path'] == absolute_path or 
                    os.path.basename(file_entry['path']) == os.path.basename(file_path)) and \
                   file_entry['session_id'] == session_id:
                    
                    # Delete the file
                    if os.path.exists(file_entry['path']):
                        try:
                            os.remove(file_entry['path'])
                        except Exception as e:
                            print(f"Error removing {file_entry['path']}: {e}")
                    
                    # Mark for removal from database
                    files_to_remove.append(file_entry)
        
        # Remove entries from database
        if files_to_remove:
            db['files'] = [f for f in db['files'] if f not in files_to_remove]
            save_file_db(db)
            
        return jsonify({'status': 'success', 'files_removed': len(files_to_remove)})
    else:
        return jsonify({'status': 'error', 'message': 'Invalid request format'})

# Endpoint for manual cleanup of expired files
@app.route('/api/cleanup/expired', methods=['GET'])
def cleanup_expired():
    """Manual trigger to clean up expired files"""
    cleanup_files()
    return jsonify({'status': 'Cleanup of expired files completed'})

# Start the background cleanup thread when the app starts
# Replace @app.before_first_request with this approach
def start_cleanup_thread():
    """Start the background cleanup thread"""
    thread = threading.Thread(target=scheduled_cleanup)
    thread.daemon = True  # Thread will terminate when main app stops
    thread.start()
    print("Background cleanup thread started")

# Create a function to initialize the app with the cleanup thread
def create_app():
    # Start the background cleanup thread
    start_cleanup_thread()
    return app

# Or if you prefer to start it directly in your main block:
if __name__ == '__main__':
    # Start the cleanup thread before running the app
    start_cleanup_thread()
    app.run(debug=True)