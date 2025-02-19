import os
from flask import Flask, request, abort
import requests
from requests.auth import HTTPBasicAuth

service_type = os.getenv('SERVICE_TYPE', 'api')
app = Flask(__name__)

if service_type == 'api':
    backend_url = os.getenv('BACKEND_URL', 'http://backend:5000')
    
    @app.route('/pay', methods=['POST'])
    def pay():
        amount = request.form.get('amount')
        if not amount:
            return "Missing parameter 'amount'", 400
        try:
            resp = requests.post(f"{backend_url}/process", data={'amount': amount})
            return resp.text, resp.status_code
        except Exception as e:
            return f"Error contacting backend: {e}", 500
    
    @app.route('/')
    def index():
        return "API Service. Use /pay to create payments."

#########################
# BACKEND
#########################
elif service_type == 'backend':
    db_url = os.getenv('DB_URL', 'http://db:5000')
    db_user = os.getenv('DB_USER', 'user')
    db_pass = os.getenv('DB_PASS', 'pass')
    
    @app.route('/process', methods=['POST'])
    def process():
        amount = request.form.get('amount')
        if not amount:
            return "Missing parameter 'amount'", 400
        try:
            resp = requests.post(f"{db_url}/store", data={'amount': amount}, auth=HTTPBasicAuth(db_user, db_pass))
            if resp.status_code == 200:
                return f"Backend:: Processed payment ({amount}). DB Response:: {resp.text}", resp.status_code
            else: return f"Backend:: Database error while saving payment. DB Response:: {resp.text}", resp.status_code
        except Exception as e:
            return f"Backend:: Error contacting database: {e}", 500

    @app.route('/')
    def index():
        return "Backend Service. Use /process to process payments."

#########################
# BATABASE
#########################
elif service_type == 'db':
    valid_user = os.getenv('DB_USER', 'user')
    valid_pass = os.getenv('DB_PASS', 'pass')

    
    def check_auth(auth):
        if not auth:
            return False
        return auth.username == valid_user and auth.password == valid_pass

    @app.route('/store', methods=['POST'])
    def store():
        auth = request.authorization
       
        if not check_auth(auth):
            abort(401, description="Unauthorized")
        amount = request.form.get('amount')
        if not amount:
            return "Missing parameter 'amount'", 400
        return f"Stored payment with value {amount}", 200

    @app.route('/')
    def index():
        return "Database Service. Use /store to store payments."

else:
    @app.route('/')
    def index():
        return f"Undefined service_type: {service_type}"

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)