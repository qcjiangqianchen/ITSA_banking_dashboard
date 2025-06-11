from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from uuid import uuid4
import os
import datetime
from sqlalchemy import Enum
import uuid
import requests
from dotenv import load_dotenv
from datetime import datetime 

load_dotenv()
app = Flask(__name__)
CORS(app) 

AWS_REGION = os.environ['AWS_REGION']
LOGGING_SERVICE_URL = os.getenv('LOGGING_SERVICE_URL', 'http://localhost:5004')
client_service_url = os.getenv('CLIENT_SERVICE_URL', 'http://localhost:5001')
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{os.environ['DB_USERNAME']}:"
    f"{os.environ['DB_PASSWORD']}@"
    f"{os.environ['DB_HOST']}:{os.getenv('DB_PORT', '3306')}/"
    f"{os.environ['DB_NAME']}"
)

db = SQLAlchemy(app)
# Client model
class Client(db.Model):
    client_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.Integer)
    address = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.Integer)
    account_status = db.Column(db.String(100), default="pending")  # Default value is 'pending'
    verification_token = db.Column(db.String(200), unique=True)  # To store the verification token

    def __init__(self, agent_id, name, date_of_birth, gender, email, phone_number, address, city, state, country, postal_code, account_status="pending"):
        self.agent_id = agent_id
        self.name = name
        self.date_of_birth = date_of_birth
        self.gender = gender
        self.email = email
        self.phone_number = phone_number
        self.address = address
        self.city = city
        self.state = state
        self.country = country
        self.postal_code = postal_code
        self.account_status = account_status

    def json(self):
        return {
            "client_id": self.client_id,
            "agent_id": self.agent_id,
            "name": self.name,
            "dob": self.date_of_birth,
            "gender": self.gender,
            "email": self.email,
            "phone_number": self.phone_number,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "country": self.country,
            "postal_code": self.postal_code,
            "account_status": self.account_status
        }
    
class Account(db.Model):
    account_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.String(36), db.ForeignKey('client.client_id'), nullable=False)
    account_type = db.Column(db.String(100), nullable=False)
    account_status = db.Column(Enum('active', 'inactive', 'deleted', name='account_status_enum'), default='active', nullable=False)
    opening_date = db.Column(db.Date, nullable=False) 
    initial_deposit = db.Column(db.Numeric(10, 2), nullable=False) 
    currency = db.Column(db.String(3), nullable=False) 
    branch_id = db.Column(db.Integer, nullable=False) 

    # Relationship to Client table (optional if you want to query client data)
    client = db.relationship('Client', backref=db.backref('accounts', lazy=True))

    def __init__(self, client_id, account_type, account_status, opening_date, initial_deposit, currency, branch_id):
        self.client_id = client_id
        self.account_type = account_type
        self.account_status = account_status
        self.opening_date = opening_date
        self.initial_deposit = initial_deposit
        self.currency = currency
        self.branch_id = branch_id

    def json(self):
        return {
            "account_id": self.account_id,
            "client_id": self.client_id,
            "account_type": self.account_type,
            "account_status": self.account_status,
            "opening_date": str(self.opening_date),
            "initial_deposit": str(self.initial_deposit),
            "currency": self.currency,
            "branch_id": self.branch_id
        }

#helper functions
def check_agent_in_client(agent_id, client_id):
    response = requests.get(f"{client_service_url}/api/clients/{client_id}")
    client = response.data
    if client and client.agent_id == agent_id:
        return True
    return False

def log_operation(operation, agent_id, client_id, attribute=None, before_value=None, after_value=None, email=None):
    try:
        # Construct log data based on the provided parameters
        log_data = {
            "operation": operation,
            "agent_id": agent_id,
            "client_id": client_id,
        }

        # Add optional fields if provided
        if attribute:
            log_data["attribute"] = attribute
        if before_value:
            log_data["before_value"] = before_value
        if after_value:
            log_data["after_value"] = after_value
        if email:
            log_data["email"] = email

        # Send POST request to logging service
        response = requests.post(LOGGING_SERVICE_URL + '/api/log/create', json=log_data)

        # Check for success status code (201)
        if response.status_code == 201:
            print("Log successfully created:", response.json())
        else:
            print(f"Failed to log operation: {response.status_code} - {response.text}")
            

    except requests.exceptions.RequestException as e:
        # Handle request exceptions (network errors, invalid URL, etc.)
        print(f"Request error: {str(e)}")

    except Exception as e:
        # Catch any other exceptions
        print(f"Error calling logging service: {str(e)}")


@app.route('/api/account/create', methods=['POST'])
# @oauth_required
def create_account():
    data = request.json
    client_id = data.get('client_id')
    agent_id = data.get('agent_id')
    account_id = uuid.uuid4()

    # Check if the agent has access to this client
    if not check_agent_in_client(agent_id, client_id):
        return jsonify({"error": "Agent does not have permissions to this client"}), 403

    account_type = data.get('account_type')
    account_status = data.get('account_status', 'active')  # Default to 'active'

    # Validate account status
    if account_status not in ['active', 'inactive', 'deleted']:
        return jsonify({"error": "Invalid account status. Valid values are 'active', 'inactive', 'deleted'."}), 400

    # Parse the date in YYYY-MM-DD format
    try:
        opening_date = datetime.strptime(data.get('opening_date'), "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD."}), 400

    initial_deposit = data.get('initial_deposit')
    currency = data.get('currency')
    branch_id = data.get('branch_id')

    # Validate required fields
    if not all([account_type, initial_deposit, currency, branch_id]):
        return jsonify({"error": "Missing required fields. 'account_type', 'initial_deposit', 'currency', and 'branch_id' are required."}), 400
    
    client = Client.query.get(client_id)
    if not client:
        return jsonify({"error": "Client not found"}), 404
    email = client.email
    
    # Create a new account
    new_account = Account(
        account_id=account_id,
        client_id=client_id,
        account_type=account_type,
        account_status=account_status,
        opening_date=opening_date,
        initial_deposit=initial_deposit,
        currency=currency,
        branch_id=branch_id
    )

    try:
        db.session.add(new_account)
        db.session.commit()

        # Log the operation
        log_operation(
            operation='CREATE',
            agent_id=agent_id,
            client_id=client_id,
            attribute='Account',
            after_value=f"ID: {account_id}",
            email=email,
        )

        return jsonify({"message": "Account created successfully", "account": new_account.json()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# delete acct
@app.route('/api/account/delete/<string:account_id>', methods=['DELETE'])
# @oauth_required
def delete_account(account_id):
    data = request.json
    client_id = data.get('client_id')
    agent_id = data.get('agent_id')

    # Check if the agent has access to this client
    if not check_agent_in_client(agent_id, client_id):
        return jsonify({"error": "Agent does not have permissions to this client"}), 403

    # Find the account by account_id and client_id
    account = Account.query.filter_by(account_id=account_id, client_id=client_id).first()
    status = account.account_status
    if not account:
        return jsonify({"error": "Account not found"}), 404
    
    client = Client.query.get(client_id)
    if not client:
        return jsonify({"error": "Client not found"}), 404
    email = client.email

    try:
        # Mark the account as deleted (soft delete)
        account.account_status = 'deleted'
        db.session.commit()

        log_operation(
            operation='DELETE',
            agent_id=agent_id,
            client_id=client_id,
            attribute='account_status',
            before_value=f"{status}",
            after_value="deleted",
            email=email,
        )

        return jsonify({"message": "Account deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
#get accounts by client id
@app.route('/api/account/get/<string:client_id>', methods=['GET'])
def get_accounts():
    client_id = request.args.get('client_id')  # Get the client_id from query parameters
    if not client_id:
        return jsonify({"error": "client_id is required"}), 400

    # Retrieve all accounts for the given client_id that are not deleted
    accounts = Account.query.filter(
        Account.client_id == client_id,
        Account.account_status != 'deleted'  # Exclude deleted accounts
    ).all()

    if not accounts:
        return jsonify({"message": "No active accounts found for this client"}), 404

    # Return the accounts as a list of JSON objects
    return jsonify({"accounts": [account.json() for account in accounts]}), 200



@app.route('/api/account/get', methods=['GET'])
def get_all_accounts():
    accounts = Account.query.filter(
        Account.account_status != 'deleted'  # Exclude deleted accounts
    ).all()

    if not accounts:
        return jsonify({"message": "No active accounts found"}), 404

    # Return the accounts as a list of JSON objects
    return jsonify({"accounts": [account.json() for account in accounts]}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5002')