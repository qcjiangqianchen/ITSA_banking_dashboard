from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
from dotenv import load_dotenv
from auth import token_required  # Assuming you have a token_required decorator in auth.py
import os
import boto3
import uuid

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{os.environ['DB_USERNAME']}:"
    f"{os.environ['DB_PASSWORD']}@"
    f"{os.environ['DB_HOST']}:{os.environ.get('DB_PORT', '3306')}/"
    f"{os.environ['DB_NAME']}"
)
db = SQLAlchemy(app)

migrate = Migrate(app, db)

COGNITO_REGION = 'ap-southeast-1'
USER_POOL_ID = 'ap-southeast-1_ImQ6I4Ypf'

cognito_client = boto3.client('cognito-idp', region_name=COGNITO_REGION)

# ✅ UPDATED User Model
class User(db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    role = db.Column(db.String(20), nullable=False)  # Admin or Agent

    def __init__(self, first_name, last_name, email, role):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.role = role

    def json(self):
        return {
            "user_id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "role": self.role
        }

# ✅ GET all users
@app.route("/api/user/get", methods=['GET'])
@token_required
def get_all_users():
    userlist = User.query.all()
    if userlist:
        return jsonify({
            "code": 200,
            "data": {
                "users": [user.json() for user in userlist]
            }
        }), 200
    else:
        return jsonify({
            "code": 404,
            "message": "There are no users"
        }), 404

# ✅ GET a user by ID
@app.route("/api/user/get/<string:user_id>", methods=['GET'])
@token_required
def get_user(user_id):
    user = User.query.get(user_id)
    if user:
        return jsonify({
            "code": 200,
            "data": user.json()
        }), 200
    else:
        return jsonify({
            "code": 404,
            "message": "User not found"
        }), 404
    
@app.route("/api/user/get_by_email", methods=["GET"])
@token_required
def get_user_by_email():
    username = request.decoded_token.get("email")

    print("Decoded username:", request.decoded_token.get("email"))

    if not username:
        return jsonify({"code": 400, "message": "Invalid token"}), 400

    user = User.query.filter_by(email=username).first()
    if user:
        return jsonify({"code": 200, "data": user.json()}), 200
    return jsonify({"code": 404, "message": "User not found"}), 404


# ✅ POST create a new user
@app.route("/api/user/create", methods=['POST'])
# @token_required
def create_user():
    try:
        data = request.get_json()
        required_fields = ["first_name", "last_name", "email", "role"]

        for field in required_fields:
            if field not in data:
                return jsonify({
                    "code": 400,
                    "message": f"Missing required field: {field}"
                }), 400
            

        first_name = data['first_name']
        last_name = data['last_name']
        email = data['email']
        role = data['role']     

        #uploading to cognito first
        response = cognito_client.admin_create_user(
            UserPoolId=USER_POOL_ID,
            Username=email,
            UserAttributes=[
                {"Name": "email", "Value": email},
                {"Name": "email_verified", "Value": "true"},
                {"Name": "name", "Value": f"{first_name} {last_name}"},
            ],
            DesiredDeliveryMediums=["EMAIL"]
        )

        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            role=role
        )

        db.session.add(new_user)
        db.session.commit()

        return jsonify({
            "code": 201,
            "message": "User created successfully",
            "data": new_user.json()
        }), 201
    
    except cognito_client.exceptions.UsernameExistsException:
        return jsonify({"message": "User already exists in cognito"}), 409
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": str(e)
        }), 500

# ✅ PUT update a user
@app.route("/api/user/update/<string:user_id>", methods=['PUT'])
@token_required
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({
            "code": 404,
            "message": "User not found"
        }), 404

    data = request.get_json()

    if 'first_name' in data:
        user.first_name = data['first_name']
    if 'last_name' in data:
        user.last_name = data['last_name']
    if 'email' in data:
        user.email = data['email']
    if 'role' in data:
        user.role = data['role']

    db.session.commit()

    return jsonify({
        "code": 200,
        "message": "User updated successfully",
        "data": user.json()
    }), 200

# ✅ DELETE a user
@app.route("/api/user/delete/<string:user_id>", methods=['DELETE'])
@token_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({
            "code": 404,
            "message": "User not found"
        }), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({
        "code": 200,
        "message": "User successfully deleted"
    }), 200

# Run the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
