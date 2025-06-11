from flask import Flask, jsonify, request
from flask_cors import CORS
import boto3
import json
import uuid
import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app) 

# S3 Configuration
S3_BUCKET_NAME = os.getenv('LOGGING_BUCKET_NAME', 'team3-crm-logs-bucket')
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID', 'your_aws_access_key')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', 'your_aws_secret_key')
AWS_REGION = os.getenv('AWS_REGION', 'ap-southeast-1')  

# SNS Topic for S3 Events
SNS_TOPIC_ARN = os.getenv('SNS_TOPIC_ARN')

# Initialize AWS clients
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

sns_client = boto3.client(
    'sns',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

# Helper Functions
def generate_log_id():
    """Generate a unique log ID"""
    return str(uuid.uuid4())

def current_timestamp():
    """Get current ISO 8601 timestamp"""
    return datetime.datetime.now().isoformat()

def store_log_in_s3(log_data):
    """Store log data in S3 bucket"""
    try:
        log_id = log_data.get('log_id')
        operation = log_data.get('operation')
        
        # Map operations to event types for event detection
        event_map = {
            'CREATE': 'AccountCreated',
            'UPDATE': 'AccountUpdate',
            'DELETE': 'AccountDisabled',
            'CLIENT_CREATE': 'ClientProfileCreated', 
            'CLIENT_UPDATE': 'ClientProfileUpdated', 
            'CLIENT_DELETE': 'ClientProfileDeleted'
        }
        
        # Add event type to the log data for SNS to filter
        log_data['event'] = event_map.get(operation)
        
        log_data['customer_id'] = log_data.get('email')
        
        changes = []
        before = log_data.get('before_value')
        after = log_data.get('after_value')

        if before and after:
            try:
                before_dict = json.loads(before.replace("'", '"'))
                after_dict = json.loads(after.replace("'", '"'))
                for key in after_dict:
                    if before_dict.get(key) != after_dict.get(key):
                        changes.append(key)
            except Exception as parse_err:
                print(f"⚠️ Could not parse before/after values: {parse_err}")

        log_data['changes'] = changes
        
        account_id = log_data.get('account_id', 'unknown')
        if changes:
            changes_str = ", ".join(changes)
            log_data['message'] = f"Customer {changes_str} has been updated in account {account_id}."
        else:
            if operation == 'CREATE':
                log_data['message'] = f"Account {account_id} has been created for customer {log_data['customer_id']}."
            elif operation == 'DELETE':
                log_data['message'] = f"Account {account_id} has been disabled for customer {log_data['customer_id']}."
            elif operation == 'CLIENT_CREATE':
                log_data['message'] = f"Client profile has been created for customer {log_data['customer_id']}."
            elif operation == 'CLIENT_UPDATE':
                log_data['message'] = f"Client profile has been updated for customer {log_data['customer_id']}."
            elif operation == 'CLIENT_DELETE':
                log_data['message'] = f"Client profile has been deleted for customer {log_data['customer_id']}."
            else:
                log_data['message'] = f"Account {account_id} was modified."
                
        # Store logs in a structure like: year/month/day/log_id.json
        now = datetime.datetime.now()
        key = f"{now.year}/{now.month:02d}/{now.day:02d}/{log_id}.json"
        
        # Convert log data to JSON string
        log_json = json.dumps(log_data)
        
        # Upload to S3
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=key,
            Body=log_json,
            ContentType='application/json',
            # Add metadata for S3 event filtering
            Metadata={
                'event-type': log_data['event'],
                'client-id': str(log_data.get('client_id', '')),
                'agent-id': str(log_data.get('agent_id', ''))
            }
        )

        # S3 event notifications should be configured to trigger SNS
        # But we can also publish directly to SNS to ensure the notification is sent
        # if operation in ['CREATE', 'UPDATE', 'DELETE']:
        #     # Prepare message for SNS
        #     notification = {
        #         'event': log_data['event'],
        #         'clientId': log_data.get('client_id'),
        #         'agentId': log_data.get('agent_id'),
        #         'message': f"Operation {operation} was performed on your account.",
        #         's3Path': {
        #             'bucket': S3_BUCKET_NAME,
        #             'key': key
        #         }
        #     }
            
        #     # Add more detail for UPDATE operations
        #     if operation == 'UPDATE' and log_data.get('attribute'):
        #         notification['message'] = f"Your {log_data.get('attribute')} was updated from '{log_data.get('before_value')}' to '{log_data.get('after_value')}'."
            
        #     # Publish to SNS
        #     sns_client.publish(
        #         TopicArn=SNS_TOPIC_ARN,
        #         Message=json.dumps(notification),
        #         MessageAttributes={
        #             'event': {
        #                 'DataType': 'String',
        #                 'StringValue': log_data['event']
        #             }
        #         }
        #     )
        
        return True, key
    except Exception as e:
        print(f"Error storing log in S3: {str(e)}")
        return False, str(e)

# API Endpoints
@app.route('/api/log/create', methods=['POST'])
def create_log():
    """Create a new log entry"""
    try:
        data = request.json
        
        # Required fields
        operation = data.get('operation')  # CREATE, READ, UPDATE, DELETE
        agent_id = data.get('agent_id')
        client_id = data.get('client_id')
        
        # For UPDATE operations
        attribute = data.get('attribute', '')  # e.g., "First Name|Address"
        before_value = data.get('before_value', '')  # e.g., "LEE|ABC"
        after_value = data.get('after_value', '')  # e.g., "TAN|XX"
        
        # Create log object
        log_data = {
            'log_id': generate_log_id(),
            'operation': operation,
            'agent_id': agent_id,
            'client_id': client_id,
            'attribute': attribute,
            'before_value': before_value,
            'after_value': after_value,
            'timestamp': current_timestamp()
        }
        
        # Store in S3 (which will trigger SNS notification)
        success, s3_result = store_log_in_s3(log_data)
        if not success:
            return jsonify({"error": f"Failed to store log in S3: {s3_result}"}), 500
        
        return jsonify({
            "message": "Log created successfully",
            "log_id": log_data['log_id'],
            "s3_path": s3_result
        }), 201
        
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/api/log/get', methods=['GET'])
def get_all_logs():
    """Retrieve all logs from the S3 bucket"""
    try:
        # Validate access permissions
        
        # Get all objects in the bucket
        all_logs = []
        
        try:
            # Use paginator to handle large number of objects
            paginator = s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(
                Bucket=S3_BUCKET_NAME,
                Prefix=""  # You can define a better prefix strategy in production
            )
            
            for page in pages:
                if 'Contents' not in page:
                    continue
                    
                for obj in page['Contents']:
                    try:
                        # Get the object
                        response = s3_client.get_object(
                            Bucket=S3_BUCKET_NAME,
                            Key=obj['Key']
                        )
                        
                        # Parse the log data
                        log_data = json.loads(response['Body'].read().decode('utf-8'))
                        
                        # Add to all logs
                        all_logs.append(log_data)
                            
                    except Exception as e:
                        print(f"Error retrieving log {obj['Key']}: {str(e)}")
            
            return jsonify({
                "logs": all_logs
            }), 200
            
        except Exception as e:
            print(f"Error listing objects in S3: {str(e)}")
            return jsonify({"error": f"Failed to retrieve logs: {str(e)}"}), 500
        
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route('/api/log/get/<client_id>', methods=['GET'])
def get_client_logs(client_id):
    """Retrieve logs for a specific client"""
    try:
        agent_id = request.args.get('agent_id')
        if not agent_id:
            return jsonify({"error": "Agent ID is required"}), 400
        
        client_logs = []
        
        try:
            # Use paginator to handle large number of objects
            paginator = s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(
                Bucket=S3_BUCKET_NAME,
                Prefix=""  # You'd need a better prefix strategy in production
            )
            
            for page in pages:
                if 'Contents' not in page:
                    continue
                    
                for obj in page['Contents']:
                    try:
                        response = s3_client.get_object(
                            Bucket=S3_BUCKET_NAME,
                            Key=obj['Key']
                        )
                        
                        log_data = json.loads(response['Body'].read().decode('utf-8'))
                        
                        if log_data.get('client_id') == client_id:
                            client_logs.append(log_data)
                            
                    except Exception as e:
                        print(f"Error retrieving log {obj['Key']}: {str(e)}")
            
            return jsonify({
                "client_id": client_id,
                "logs": client_logs
            }), 200
            
        except Exception as e:
            print(f"Error listing objects in S3: {str(e)}")
            return jsonify({"error": f"Failed to retrieve logs: {str(e)}"}), 500
        
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/api/log/search', methods=['GET'])
def search_logs():
    """Search logs with filters"""
    try:
        # Get search parameters
        client_id = request.args.get('client_id')
        agent_id = request.args.get('agent_id')
        operation = request.args.get('operation')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Real implementation of search in S3
        matching_logs = []
        
        # Convert start and end dates to datetime objects if provided
        start_datetime = None
        end_datetime = None
        
        if start_date:
            start_datetime = datetime.datetime.fromisoformat(start_date)
        
        if end_date:
            end_datetime = datetime.datetime.fromisoformat(end_date)
        
        # List objects in S3
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(
            Bucket=S3_BUCKET_NAME,
            Prefix=""  # You'd need a better prefix strategy in production
        )
        
        for page in pages:
            if 'Contents' not in page:
                continue
                
            for obj in page['Contents']:
                try:
                    response = s3_client.get_object(
                        Bucket=S3_BUCKET_NAME,
                        Key=obj['Key']
                    )
                    
                    log_data = json.loads(response['Body'].read().decode('utf-8'))
                    
                    # Filter logs based on criteria
                    include_log = True
                    
                    if client_id and log_data.get('client_id') != client_id:
                        include_log = False
                    
                    if agent_id and log_data.get('agent_id') != agent_id:
                        include_log = False
                    
                    if operation and log_data.get('operation') != operation:
                        include_log = False
                    
                    if start_datetime:
                        log_datetime = datetime.datetime.fromisoformat(log_data.get('timestamp').split('.')[0])
                        if log_datetime < start_datetime:
                            include_log = False
                    
                    if end_datetime:
                        log_datetime = datetime.datetime.fromisoformat(log_data.get('timestamp').split('.')[0])
                        if log_datetime > end_datetime:
                            include_log = False
                    
                    if include_log:
                        matching_logs.append(log_data)
                        
                except Exception as e:
                    print(f"Error retrieving log {obj['Key']}: {str(e)}")
        
        return jsonify({
            "logs": matching_logs,
            "count": len(matching_logs)
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# Create endpoint to manually configure S3 event notifications
@app.route('/api/log/admin/setup-event-notifications', methods=['POST'])
def setup_event_notifications():
    """Set up S3 event notifications to SNS"""
    try:
        s3_client.put_bucket_notification_configuration(
            Bucket=S3_BUCKET_NAME,
            NotificationConfiguration={
                'TopicConfigurations': [
                    {
                        'TopicArn': SNS_TOPIC_ARN,
                        'Events': ['s3:ObjectCreated:*'],
                        'Filter': {
                            'Key': {
                                'FilterRules': [
                                    {
                                        'Name': 'suffix',
                                        'Value': '.json'
                                    }
                                ]
                            }
                        }
                    }
                ]
            }
        )
        
        return jsonify({
            "message": "S3 event notifications configured successfully"
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to configure S3 event notifications: {str(e)}"}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    try:
        s3_client.head_bucket(Bucket=S3_BUCKET_NAME)
        print(f"S3 bucket {S3_BUCKET_NAME} exists")
    except:
        print(f"Creating S3 bucket {S3_BUCKET_NAME}...")
        s3_client.create_bucket(
            Bucket=S3_BUCKET_NAME,
            CreateBucketConfiguration={'LocationConstraint': AWS_REGION}
        )
        print(f"S3 bucket {S3_BUCKET_NAME} created")
    
    app.run(host='0.0.0.0', port=5004, debug=True)