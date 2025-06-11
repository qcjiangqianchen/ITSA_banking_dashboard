from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
# from flask_migrate import Migrate
from dotenv import load_dotenv
import os
import uuid

load_dotenv()

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{os.environ['DB_USERNAME']}:"
    f"{os.environ['DB_PASSWORD']}@"
    f"{os.environ['DB_HOST']}:{os.environ.get('DB_PORT', '3306')}/"
    f"{os.environ['DB_NAME']}"
)
db = SQLAlchemy(app)

# migrate = Migrate(app, db)


# ✅ UPDATED User Model
class AdminActionLog(db.Model):
    __tablename__ = 'admin_action_logs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    admin_name = db.Column(db.String(100), nullable=False)
    target_name = db.Column(db.String(100), nullable=False)
    target_role = db.Column(db.String(20), nullable=False)
    action_type = db.Column(db.String(20), nullable=False)  # CREATE, UPDATE, DELETE
    timestamp = db.Column(db.DateTime, default=db.func.now())

    def __init__(self, admin_name, target_name, target_role, action_type):
        self.admin_name = admin_name
        self.target_name = target_name
        self.target_role = target_role
        self.action_type = action_type

    def json(self):
        return {
            "id": self.id,
            "admin_name": self.admin_name,
            "target_name": self.target_name,
            "target_role": self.target_role,
            "action_type": self.action_type,
            "timestamp": self.timestamp.isoformat()
        }
    
# ============================
# ✅ POST Log an Admin Action
# ============================
@app.route("/api/admin/log", methods=['POST'])
def log_admin_action():
    data = request.get_json()

    required = ['admin_name', 'action_type', 'target_role', 'target_name']
    if not all(k in data for k in required):
        return jsonify({"code": 400, "message": "Missing required log fields"}), 400

    log = AdminActionLog(
        admin_name=data['admin_name'],
        action_type=data['action_type'],
        target_role=data['target_role'],
        target_name=data['target_name']
    )

    db.session.add(log)
    db.session.commit()

    return jsonify({"code": 201, "message": "Action logged", "data": log.json()}), 201

# ============================
# ✅ GET All Admin Logs
# ============================
@app.route("/api/admin/logs", methods=['GET'])
def get_all_logs():
    logs = AdminActionLog.query.order_by(AdminActionLog.timestamp.desc()).all()
    return jsonify({"code": 200, "data": [log.json() for log in logs]}), 200

# ============================
# ✅ GET Logs by Admin Name
# ============================
@app.route("/api/admin/logs/<string:admin_name>", methods=['GET'])
def get_logs_by_admin(admin_name):
    logs = AdminActionLog.query.filter_by(admin_name=admin_name).order_by(AdminActionLog.timestamp.desc()).all()
    return jsonify({"code": 200, "data": [log.json() for log in logs]}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # This will create tables if they don't exist
    app.run(host='0.0.0.0', port=5020, debug=True)