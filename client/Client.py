import hashlib
import time
from flask import Flask, jsonify, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
from uuid import uuid4
import requests
import boto3
import json
from email_validator import validate_email, EmailNotValidError
from datetime import datetime
from dotenv import load_dotenv
import os
import uuid
# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)


# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{os.environ['DB_USERNAME']}:"
    f"{os.environ['DB_PASSWORD']}@"
    f"{os.environ['DB_HOST']}:{os.environ.get('DB_PORT', '3306')}/"
    f"{os.environ['DB_NAME']}"
)
db = SQLAlchemy(app)

# AWS SQS Configuration
sqs = boto3.client(
    'sqs',
    region_name=os.environ.get('AWS_REGION', 'ap-southeast-1'),
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
)

queue_url = os.environ['SQS_QUEUE_URL']

# Logging service URL
LOGGING_SERVICE_URL = os.environ.get('LOGGING_SERVICE_URL')
APP_BASE_URL = os.environ.get('APP_BASE_URL')
# Client model
class Client(db.Model):
    client_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = db.Column(db.String(36), nullable=False)
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

# Helper functions
def check_agent_in_client(agent_id, client_id):
    client = Client.query.filter_by(client_id=client_id).first()
    return client and client.agent_id == agent_id


def generate_verification_token():
    """ Generate a unique token for the verification link """
    return hashlib.sha256(str(time.time()).encode()).hexdigest()

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


def is_valid_email(email):
    try:
        # Validate and normalize the email
        valid = validate_email(email)
        return True
    except EmailNotValidError as e:
        print(str(e))
        return False        

# Function to send email event to SQS
def send_verification_email_to_sqs(customer_id, event_type, message):
    # Create the event message to be sent to SQS
    event_data = {
        'customerId': customer_id,
        'event': event_type,
        'message': message
    }
    # Send the message to the SQS queue
    try:
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(event_data)
        )
        print(f"Verification email event sent to SQS: {response}")
    except Exception as e:
        print(f"Error sending message to SQS: {e}")

def is_valid_date(date_string):
    """Check if the date is in YYYY-MM-DD format and valid."""
    try:
        # Parse the date string into a datetime object
        datetime.strptime(date_string, "%Y-%m-%d")
        return True
    except ValueError:
        return False
    

# Middleware to handle CORS preflight requests
@app.before_request
def handle_options():
    if request.method == 'OPTIONS':
        return '', 200


# Routes
@app.route('/api/client/get/agent/<string:agent_id>', methods=['GET'])
def get_clients_by_agent(agent_id):
    try:
        clients = Client.query.filter_by(agent_id=agent_id).all()
        
        return jsonify([client.json() for client in clients]), 200
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    

@app.route('/api/client/create', methods=['POST', 'OPTIONS'])
def create_client_profile():
    data = request.json
    client_id = uuid.uuid4()
    agent_id = data.get('agent_id')
    name = data.get('name')
    dob = data.get('dob')
    if not is_valid_date(dob):
        return jsonify({"error": "Invalid date of birth format. Use YYYY-MM-DD."}), 400
    gender = data.get('gender')
    email = data.get('email')

    # Validate email
    if not is_valid_email(email):
        return jsonify({"error": "Invalid email address"}), 400
    
    phone_number = data.get('phone_number')
    address = data.get('address')
    city = data.get('city')
    state = data.get('state')
    country = data.get('country', 'Singapore')
    postal_code = data.get('postal_code')

    # Generate verification token
    verification_token = generate_verification_token()

    new_client = Client(
        client_id=client_id,
        agent_id=agent_id,
        name=name,
        date_of_birth=dob,
        gender=gender,
        email=email,
        phone_number=phone_number,
        address=address,
        city=city,
        state=state,
        country=country,
        postal_code=postal_code,
        account_status="pending",
        verification_token=verification_token  # Store the token in the database
    )
    try:
        db.session.add(new_client)
        db.session.commit()

        # Log the operation
        log_operation("CLIENT_CREATE", agent_id, client_id, email=email)

        # Send a verification email event to SQS
        verification_url = f"{APP_BASE_URL}/api/clients/{client_id}/verify/{verification_token}"

        message = f"Please verify your email address by clicking the following link: {verification_url}"
        send_verification_email_to_sqs(
            customer_id=email,
            event_type="AccountVerification",
            message=message
        )

        return jsonify({"message": "Client profile created successfully", "client_id": client_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An error occurred while creating the client profile: {str(e)}"}), 500


@app.route('/api/client/verify/<string:client_id>/<verification_token>', methods=['GET'])
def verify_account(client_id, verification_token):
    # Fetch client by ID
    client = Client.query.filter_by(client_id=client_id).first()
    
    if not client:
        return jsonify({"error": "Client not found"}), 404

    # Check if the verification token matches
    if client.verification_token != verification_token:
        return jsonify({"error": "Invalid or expired verification token"}), 400

    # Update account status to verified
    agent_id=client.agent_id
    client.account_status = "verified"
    client.verification_token = None  # Clear the verification token
    db.session.commit()
    log_operation("CLIENT_UPDATE", agent_id, client_id, "account_status", "pending", "verified", email=client.email)
    return jsonify({"message": "Account verified successfully"}), 200

@app.route('/api/client/update/<string:client_id>', methods=['PUT', 'OPTIONS'])
def update_client_information(client_id):
    data = request.json
    agent_id = data['agent_id']
    if not check_agent_in_client(agent_id, client_id):
        return jsonify({"error": "Agent does not have permissions to update this client"}), 403

    client = Client.query.filter_by(client_id=client_id).first()
    if not client:
        return jsonify({"error": "Client not found"}), 404

    before_values = client.json()
    client.name = data.get('name', client.name)
    client.date_of_birth = data.get('dob', client.date_of_birth)
    client.gender = data.get('gender', client.gender)
    client.email = data.get('email', client.email)
    client.phone_number = data.get('phone_number', client.phone_number)
    client.address = data.get('address', client.address)
    client.city = data.get('city', client.city)
    client.state = data.get('state', client.state)
    client.country = data.get('country', client.country)
    client.postal_code = data.get('postal_code', client.postal_code)

    try:
        db.session.commit()

        # Log the operation
        log_operation("CLIENT_UPDATE", agent_id, client_id, attribute="Client Info", before_value=str(before_values), after_value=str(client.json()), email=client.email)

        return jsonify({"message": "Client information updated successfully", "client_id": client_id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An error occurred while updating the client profile: {str(e)}"}), 500

@app.route('/api/clients/delete/<string:client_id>', methods=['DELETE', 'OPTIONS'])

def delete_client_profile(client_id):
    data = request.json
    agent_id = data['agent_id']

    client = Client.query.filter_by(client_id=client_id).first()
    if not client:
        return jsonify({"error": "Client not found"}), 404

    if client.agent_id != agent_id:
        return jsonify({"error": "Agent does not have permission to delete this client"}), 403

    client.account_status = "deleted"
    db.session.commit()
    log_operation("CLIENT_DELETE", agent_id, client_id, email=client.email)
    return jsonify({"message": "Client profile deleted successfully (soft delete)"}), 200

@app.route('/api/client/get/all', methods=['GET'])
def get_all_clients():
    try:
        clients = Client.query.all()  # Retrieves all clients from the database
        return jsonify([client.json() for client in clients]), 200
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)