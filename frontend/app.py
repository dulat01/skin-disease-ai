"""
Frontend Web Application
Flask app serving web GUI - proxies all API calls to backend microservices via API Gateway
"""

from flask import Flask, render_template, request, jsonify, session
from werkzeug.utils import secure_filename
import requests
import os
from pathlib import Path
import uuid

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'skin-disease-secret-key-change-in-prod')
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max

# All requests go through API Gateway for auth, rate limiting, circuit breaking
API_GATEWAY_URL = os.environ.get('API_GATEWAY_URL', 'http://api-gateway:8000')
# Direct prediction service URL for anonymous users (gateway requires JWT)
PREDICTION_SERVICE_URL = os.environ.get('PREDICTION_SERVICE_URL', 'http://prediction-service:8002')

UPLOAD_FOLDER = '/tmp/uploads'
Path(UPLOAD_FOLDER).mkdir(exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def get_auth_headers():
    """Return Authorization header if user is logged in"""
    token = session.get('access_token')
    if token:
        return {'Authorization': f'Bearer {token}'}
    return {}


@app.route('/')
def index():
    return render_template('index.html')


# =============================================================================
# AUTH ROUTES - proxy to API Gateway → Auth Service
# =============================================================================

@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        resp = requests.post(
            f"{API_GATEWAY_URL}/api/v1/auth/register",
            json=data,
            timeout=10
        )
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({'success': False, 'error': 'Cannot connect to backend'}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        resp = requests.post(
            f"{API_GATEWAY_URL}/api/v1/auth/login",
            json=data,
            timeout=10
        )
        result = resp.json()

        if resp.status_code == 200 and result.get('success'):
            tokens = result['data']['tokens']
            session['access_token'] = tokens['access_token']
            session['refresh_token'] = tokens['refresh_token']
            session['user'] = result['data']['user']

        return jsonify(result), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({'success': False, 'error': 'Cannot connect to backend'}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    try:
        refresh_token = session.get('refresh_token')
        if refresh_token:
            requests.post(
                f"{API_GATEWAY_URL}/api/v1/auth/logout",
                json={'refresh_token': refresh_token},
                headers=get_auth_headers(),
                timeout=5
            )
    except Exception:
        pass
    finally:
        session.clear()
    return jsonify({'success': True, 'message': 'Logged out'})


@app.route('/api/auth/me', methods=['GET'])
def get_me():
    user = session.get('user')
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    return jsonify({'success': True, 'data': user})


# =============================================================================
# PREDICTION ROUTES
# =============================================================================

@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image provided'}), 400

        image = request.files['image']
        if not image.filename:
            return jsonify({'success': False, 'error': 'No image selected'}), 400

        if not image.content_type or not image.content_type.startswith('image/'):
            return jsonify({'success': False, 'error': 'File must be an image'}), 400

        filename = secure_filename(image.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
        image.save(filepath)

        try:
            with open(filepath, 'rb') as f:
                files = {'image': (filename, f, image.content_type or 'image/jpeg')}

                if session.get('access_token'):
                    # Authenticated: go through API Gateway (JWT is validated, X-User-ID set from token)
                    resp = requests.post(
                        f"{API_GATEWAY_URL}/api/v1/predictions/",
                        files=files,
                        headers=get_auth_headers(),
                        timeout=60
                    )
                else:
                    # Anonymous: call prediction service directly with random user ID
                    resp = requests.post(
                        f"{PREDICTION_SERVICE_URL}/api/v1/predictions/",
                        files=files,
                        headers={'X-User-ID': str(uuid.uuid4())},
                        timeout=60
                    )
        finally:
            try:
                os.remove(filepath)
            except Exception:
                pass

        if resp.status_code in (200, 201):
            return jsonify(resp.json())

        try:
            err = resp.json()
            msg = err.get('detail') or err.get('error') or 'Prediction failed'
        except Exception:
            msg = 'Prediction failed'
        return jsonify({'success': False, 'error': msg}), resp.status_code

    except requests.exceptions.ConnectionError:
        return jsonify({'success': False, 'error': 'Cannot connect to backend. Is the backend running?'}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/predictions/history', methods=['GET'])
def get_history():
    if not session.get('access_token'):
        return jsonify({'success': False, 'error': 'Authentication required'}), 401

    try:
        resp = requests.get(
            f"{API_GATEWAY_URL}/api/v1/predictions/history",
            params={
                'page': request.args.get('page', 1),
                'page_size': request.args.get('page_size', 20)
            },
            headers=get_auth_headers(),
            timeout=10
        )
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({'success': False, 'error': 'Cannot connect to backend'}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/predictions/<prediction_id>/feedback', methods=['POST'])
def submit_feedback(prediction_id):
    if not session.get('access_token'):
        return jsonify({'success': False, 'error': 'Authentication required'}), 401

    try:
        resp = requests.post(
            f"{API_GATEWAY_URL}/api/v1/predictions/{prediction_id}/feedback",
            json=request.get_json(),
            headers=get_auth_headers(),
            timeout=10
        )
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({'success': False, 'error': 'Cannot connect to backend'}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# PROFILE ROUTES - patient profile management
# =============================================================================

@app.route('/api/profile', methods=['GET'])
def get_profile():
    if not session.get('access_token'):
        return jsonify({'success': False, 'error': 'Authentication required'}), 401

    try:
        resp = requests.get(
            f"{API_GATEWAY_URL}/api/v1/auth/profile",
            headers=get_auth_headers(),
            timeout=10
        )
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({'success': False, 'error': 'Cannot connect to backend'}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/profile', methods=['PUT'])
def update_profile():
    if not session.get('access_token'):
        return jsonify({'success': False, 'error': 'Authentication required'}), 401

    try:
        data = request.get_json()
        resp = requests.put(
            f"{API_GATEWAY_URL}/api/v1/auth/profile",
            json=data,
            headers=get_auth_headers(),
            timeout=10
        )
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({'success': False, 'error': 'Cannot connect to backend'}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# DOCTOR & SUBSCRIPTION ROUTES
# =============================================================================

@app.route('/api/doctors/register', methods=['POST'])
def register_doctor():
    try:
        data = request.get_json()
        resp = requests.post(
            f"{API_GATEWAY_URL}/api/v1/auth/doctors/register",
            json=data,
            timeout=10
        )
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({'success': False, 'error': 'Cannot connect to backend'}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/doctors/login', methods=['POST'])
def login_doctor():
    try:
        data = request.get_json()
        resp = requests.post(
            f"{API_GATEWAY_URL}/api/v1/auth/doctors/login",
            json=data,
            timeout=10
        )
        result = resp.json()

        if resp.status_code == 200 and result.get('success'):
            tokens = result['data'].get('access_token')
            session['doctor_token'] = tokens
            session['doctor'] = result['data']['doctor']

        return jsonify(result), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({'success': False, 'error': 'Cannot connect to backend'}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/subscription/plans', methods=['GET'])
def get_subscription_plans():
    try:
        resp = requests.get(
            f"{API_GATEWAY_URL}/api/v1/public/subscription/plans",
            timeout=10
        )
        result = resp.json()
        return jsonify(result), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({'success': False, 'error': 'Cannot connect to backend'}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/subscription/request', methods=['POST'])
def request_subscription():
    try:
        data = request.get_json()
        # Use public endpoint - no authentication required
        resp = requests.post(
            f"{API_GATEWAY_URL}/api/v1/public/subscription/request",
            json=data,
            timeout=10
        )
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({'success': False, 'error': 'Cannot connect to backend'}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/subscription/status', methods=['GET'])
def get_subscription_status():
    if not session.get('access_token'):
        return jsonify({'success': False, 'error': 'Authentication required'}), 401

    try:
        resp = requests.get(
            f"{API_GATEWAY_URL}/api/v1/auth/subscription/status",
            headers=get_auth_headers(),
            timeout=10
        )
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({'success': False, 'error': 'Cannot connect to backend'}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# ADMIN ROUTES
# =============================================================================

@app.route('/api/admin/doctors', methods=['GET'])
def admin_list_doctors():
    if not session.get('access_token'):
        return jsonify({'success': False, 'error': 'Authentication required'}), 401

    try:
        resp = requests.get(
            f"{API_GATEWAY_URL}/api/v1/auth/admin/doctors",
            params={'verified_only': request.args.get('verified_only', 'false')},
            headers=get_auth_headers(),
            timeout=10
        )
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/doctors/<doctor_id>/verify', methods=['POST'])
def admin_verify_doctor(doctor_id):
    if not session.get('access_token'):
        return jsonify({'success': False, 'error': 'Authentication required'}), 401

    try:
        resp = requests.post(
            f"{API_GATEWAY_URL}/api/v1/auth/admin/doctors/{doctor_id}/verify",
            headers=get_auth_headers(),
            timeout=10
        )
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/subscription-requests', methods=['GET'])
def admin_list_subscription_requests():
    if not session.get('access_token'):
        return jsonify({'success': False, 'error': 'Authentication required'}), 401

    try:
        resp = requests.get(
            f"{API_GATEWAY_URL}/api/v1/auth/admin/subscription-requests",
            params={'status': request.args.get('status', 'pending')},
            headers=get_auth_headers(),
            timeout=10
        )
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/subscription-requests/<request_id>/approve', methods=['POST'])
def admin_approve_subscription(request_id):
    if not session.get('access_token'):
        return jsonify({'success': False, 'error': 'Authentication required'}), 401

    try:
        resp = requests.post(
            f"{API_GATEWAY_URL}/api/v1/auth/admin/subscription-requests/{request_id}/approve",
            headers=get_auth_headers(),
            timeout=10
        )
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/subscription-requests/<request_id>/decline', methods=['POST'])
def admin_decline_subscription(request_id):
    if not session.get('access_token'):
        return jsonify({'success': False, 'error': 'Authentication required'}), 401

    try:
        data = request.get_json() or {}
        resp = requests.post(
            f"{API_GATEWAY_URL}/api/v1/auth/admin/subscription-requests/{request_id}/decline",
            json=data,
            headers=get_auth_headers(),
            timeout=10
        )
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# HEALTH
# =============================================================================

@app.route('/api/health', methods=['GET'])
def health():
    try:
        resp = requests.get(f"{API_GATEWAY_URL}/health", timeout=5)
        if resp.status_code == 200:
            return jsonify({'status': 'healthy', 'backend': resp.json()})
        return jsonify({'status': 'unhealthy'}), 503
    except Exception:
        return jsonify({'status': 'backend_unavailable'}), 503


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=False)
