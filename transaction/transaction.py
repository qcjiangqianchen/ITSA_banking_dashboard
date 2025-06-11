from flask import Flask, jsonify, request  # Flask web framework
from flask_cors import CORS  # Cross-Origin Resource Sharing
from dotenv import load_dotenv  # To load environment variables from .env file
from database_singleton import DatabaseSingleton  # Singleton class for DB connection
import os  # Operating system interaction
import paramiko  # For SFTP connection
import csv  # For reading CSV files

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS to allow API access from frontend

# Configure Database using environment variables
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{os.getenv('DB_USERNAME')}:"
    f"{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '3306')}/"
    f"{os.getenv('DB_NAME')}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable track modifications to save resources

# Initialize Singleton Database Instance
db_instance = DatabaseSingleton(app)
db = db_instance.db  # Get SQLAlchemy database instance

# Define the Transaction model (ORM)
class Transaction(db.Model):
    __tablename__ = 'transactions'

    # Define table columns
    id = db.Column(db.String(50), primary_key=True)  # Transaction ID
    client_id = db.Column(db.String(50), nullable=False)  # Client ID
    transaction_type = db.Column(db.String(1), nullable=False)  # D = Deposit, W = Withdrawal
    amount = db.Column(db.Float, nullable=False)  # Transaction amount
    date = db.Column(db.String(100), nullable=False)  # Date of transaction
    status = db.Column(db.String(50), nullable=False)  # Status: Completed, Pending, Failed

    # Utility method to convert object to JSON format for API responses
    def to_json(self):
        return {
            "id": self.id,
            "client_id": self.client_id,
            "transaction_type": self.transaction_type,
            "amount": self.amount,
            "date": self.date,
            "status": self.status
        }

# Create all tables if they do not exist yet
with app.app_context():
    db.create_all()

# Function to securely download CSV file from the SFTP server
def fetch_csv_from_sftp(remote_path, local_path):
    # Get SFTP connection details from environment variables
    host = os.getenv("SFTP_HOST")
    port = int(os.getenv("SFTP_PORT", 22))
    username = os.getenv("SFTP_USERNAME")
    password = os.getenv("SFTP_PASSWORD")

    # Set up the SFTP connection
    transport = paramiko.Transport((host, port))
    transport.connect(username=username, password=password)

    # Open SFTP session and download the file
    sftp = paramiko.SFTPClient.from_transport(transport)
    sftp.get(remote_path, local_path)

    # Close SFTP session and transport
    sftp.close()
    transport.close()

# Function to read, validate, and store CSV data in the database
def parse_and_store_csv(csv_path):
    valid_types = ["D", "W"]  # Valid transaction types
    valid_statuses = ["Completed", "Pending", "Failed"]  # Valid status types
    skipped_rows = []  # List to collect invalid rows for logging

    # Open and read the CSV file
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                # Validation checks
                if row["transaction_type"] not in valid_types:
                    row["error"] = "Invalid transaction type"
                    skipped_rows.append(row)
                    continue

                if row["status"] not in valid_statuses:
                    row["error"] = "Invalid transaction status"
                    skipped_rows.append(row)
                    continue

                amount = float(row["amount"])
                if amount <= 0:
                    row["error"] = "Amount must be positive"
                    skipped_rows.append(row)
                    continue

                # Prepare transaction object
                txn = Transaction(
                    id=row["transaction_id"],
                    client_id=row["client_id"],
                    transaction_type=row["transaction_type"],
                    amount=amount,
                    date=row["date"],
                    status=row["status"]
                )
                # Merge: insert or update if existing
                db.session.merge(txn)

            except Exception as e:
                # Log row with error
                row["error"] = str(e)
                skipped_rows.append(row)

        # Commit all changes to the database
        db.session.commit()

    # Log skipped rows (optional: useful for debugging)
    if skipped_rows:
        print(f"Skipped {len(skipped_rows)} row(s) due to validation errors.")
        for r in skipped_rows:
            print(r)

# API route: Fetch and process transactions from SFTP
@app.route('/api/transaction/fetch', methods=['POST'])
def fetch_transactions():
    try:
        remote_path = '/upload/transactions.csv'  # SFTP path
        local_path = 'downloaded_transactions.csv'  # Local save path

        fetch_csv_from_sftp(remote_path, local_path)  # Download CSV file
        parse_and_store_csv(local_path)  # Process and store transactions

        return jsonify({"code": 200, "message": "Transactions imported successfully."}), 200
    except Exception as e:
        return jsonify({"code": 500, "message": str(e)}), 500

# API route: Get transactions for a specific client
@app.route('/api/transaction/get/<client_id>', methods=['GET'])
def get_transactions(client_id):
    # Query database for transactions by client ID
    transactions = Transaction.query.filter_by(client_id=client_id).all()
    return jsonify({
        "code": 200,
        "data": [txn.to_json() for txn in transactions]
    })

# API route: Get all transactions
@app.route('/api/transaction/get', methods=['GET'])
def get_all_transactions():
    # Query all transactions from database
    transactions = Transaction.query.all()
    return jsonify({
        "code": 200,
        "data": [txn.to_json() for txn in transactions]
    }), 200

# Run the Flask application
if __name__ == '__main__':
    # Run app accessible from outside container
    app.run(host='0.0.0.0', port=5003, debug=True)