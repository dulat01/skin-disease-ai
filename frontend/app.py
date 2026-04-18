"""
Frontend Web Application
Flask app serving web GUI and handling predictions
"""

from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import requests
import os
from pathlib import Path

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max

# Backend service URLs (internal Docker network)
# For web frontend, we bypass API gateway and call prediction service directly
PREDICTION_SERVICE_URL = os.getenv('PREDICTION_SERVICE_URL', 'http://prediction-service:8002')
UPLOAD_FOLDER = '/tmp/uploads'

Path(UPLOAD_FOLDER).mkdir(exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/predict', methods=['POST'])
def predict():
    """Handle prediction request"""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400

        image = request.files['image']
        if image.filename == '':
            return jsonify({'error': 'No image selected'}), 400

        # Validate image type
        if not image.content_type.startswith('image/'):
            return jsonify({'error': 'File must be an image'}), 400

        # Save temporarily
        filename = secure_filename(image.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(filepath)

        # Send to backend
        with open(filepath, 'rb') as f:
            files = {'image': (filename, f, 'image/jpeg')}
            headers = {'X-User-ID': 'web-user'}

            response = requests.post(
                f"{PREDICTION_SERVICE_URL}/api/v1/predictions/",
                files=files,
                headers=headers,
                timeout=30
            )

        # Clean up
        try:
            os.remove(filepath)
        except:
            pass

        if response.status_code == 201:
            result = response.json()
            return jsonify(result)
        else:
            return jsonify({'error': f'Prediction failed: {response.text}'}), response.status_code

    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Cannot connect to backend. Check if backend services are running.'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Check backend health"""
    try:
        # Check prediction service health
        response = requests.get(f"{PREDICTION_SERVICE_URL}/health", timeout=5)
        if response.status_code == 200:
            return jsonify({'status': 'healthy', 'backend': response.json()})
        else:
            return jsonify({'status': 'unhealthy'}), 503
    except:
        return jsonify({'status': 'backend_unavailable'}), 503

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=False)
