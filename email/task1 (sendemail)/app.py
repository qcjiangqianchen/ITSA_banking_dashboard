import boto3
import json
import time
import logging
import re
import os
from flask import Flask, jsonify
import threading

# Load environment variables
AWS_REGION = os.getenv('AWS_REGION', 'ap-southeast-1')
SQS_QUEUE_URL = os.getenv('SQS_QUEUE_URL')
STAFF_EMAIL = os.getenv('STAFF_EMAIL', 'itsateam3@gmail.com')

# AWS clients
sqs = boto3.client('sqs', region_name=AWS_REGION)
ses = boto3.client('ses', region_name=AWS_REGION)

# Logging setup
logging.basicConfig(level=logging.INFO)

MAX_RETRIES = 10  # Retry attempts for sending emails

app = Flask(__name__)

def format_event_type(event_type, for_subject=False):
    formatted = re.sub(r'([a-z])([A-Z])', r'\1 \2', event_type)
    return formatted.title() if for_subject else formatted.lower()

def get_email_template(event_type, message):
    """Return subject and body template based on event type"""
    
    templates = {
        "AccountUpdate": {
            "subject": "Account Update Notification",
            "body": (
                f"Dear Customer,\n\n"
                f"Your account has been updated successfully.\n\n"
                f"{message}\n\n"
                f"If you did not authorize this change, please contact our support team immediately.\n\n"
                f"Best regards,\n"
                f"Scrooge Bank"
            )
        },
        "AccountCreated": {
            "subject": "Welcome to Scrooge Bank",
            "body": (
                f"Dear Customer,\n\n"
                f"Welcome to Scrooge Bank! Your new account has been created successfully.\n\n"
                f"{message}\n\n"
                f"You can now log in to our online banking portal to view your account details and start managing your finances.\n\n"
                f"If you have any questions, our customer support team is here to help.\n\n"
                f"Best regards,\n"
                f"Scrooge Bank"
            )
        },
        "AccountDisabled": {
            "subject": "Account Disabled Notification",
            "body": (
                f"Dear Customer,\n\n"
                f"Your account has been disabled.\n\n"
                f"{message}\n\n"
                f"If you have any questions or believe this was done in error, please contact our customer support team for assistance.\n\n"
                f"Best regards,\n"
                f"Scrooge Bank"
            )
        },
        "ClientProfileCreated": {
            "subject": "Client Profile Created Successfully",
            "body": (
                f"Dear Customer,\n\n"
                f"Your client profile has been successfully created with Scrooge Bank.\n\n"
                f"{message}\n\n"
                f"Your profile information helps us provide you with personalized services tailored to your financial needs.\n\n"
                f"Best regards,\n"
                f"Scrooge Bank"
            )
        },
        "ClientProfileUpdated": {
            "subject": "Client Profile Update Confirmation",
            "body": (
                f"Dear Customer,\n\n"
                f"Your client profile has been updated successfully.\n\n"
                f"{message}\n\n"
                f"If you did not make these changes, please contact our support team immediately.\n\n"
                f"Best regards,\n"
                f"Scrooge Bank"
            )
        },
        "ClientProfileDeleted": {
            "subject": "Client Profile Deletion Confirmation",
            "body": (
                f"Dear Customer,\n\n"
                f"Your client profile has been deleted from our system as requested.\n\n"
                f"{message}\n\n"
                f"We're sorry to see you go. If you wish to create a new profile in the future, you are welcome to do so.\n\n"
                f"Best regards,\n"
                f"Scrooge Bank"
            )
        }
    }
    
    # Return default template if event type not found
    if event_type not in templates:
        return {
            "subject": f"{format_event_type(event_type, for_subject=True)} Notification",
            "body": (
                f"Dear Customer,\n\n"
                f"An event regarding your account has occurred: {format_event_type(event_type, for_subject=False)}.\n\n"
                f"{message}\n\n"
                f"Best regards,\n"
                f"Scrooge Bank"
            )
        }
    
    return templates[event_type]

def send_email(event_type, recipient_email, message):
    if not recipient_email or not re.match(r"[^@]+@[^@]+\.[^@]+", recipient_email):
        logging.error(f"Invalid recipient email: {recipient_email}")
        return {"error": "Invalid email format"}, 400

    template = get_email_template(event_type, message)
    
    try:
        response = ses.send_email(
            Source=STAFF_EMAIL,
            Destination={'ToAddresses': [recipient_email]},
            Message={
                'Subject': {'Data': template["subject"]},
                'Body': {'Text': {'Data': template["body"]}}
            }
        )
        logging.info(f"Email sent successfully to {recipient_email} for event {event_type}")
        return response
    except Exception as e:
        logging.error(f"Error sending email to {recipient_email}: {e}")
        return {"error": str(e)}, 500

def process_sqs():
    try:
        while True:  # Infinite loop for continuous polling
            response = sqs.receive_message(
                QueueUrl=SQS_QUEUE_URL,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=20,
                MessageAttributeNames=['All']
            )

            if 'Messages' not in response:
                logging.info("No messages in the queue")
                time.sleep(5)  # Sleep before retrying if no messages are found
                continue

            for message in response['Messages']:
                try:
                    sns_message = json.loads(message['Body'])

                    event_type = sns_message.get('event')
                    customer_email = sns_message.get('customerId')
                    message_content = sns_message.get('message')

                    # Support for all event types
                    valid_events = [
                        "AccountUpdate", "AccountCreated", "AccountDisabled",
                        "ClientProfileCreated", "ClientProfileUpdated", "ClientProfileDeleted"
                    ]
                    
                    if event_type in valid_events:
                        retries = 0
                        while retries < MAX_RETRIES:
                            try:
                                send_email(event_type, customer_email, message_content)
                                receipt_handle = message['ReceiptHandle']
                                sqs.delete_message(QueueUrl=SQS_QUEUE_URL, ReceiptHandle=receipt_handle)
                                logging.info(f"Message processed and deleted from SQS: {event_type}")
                                break  # Break out of the retry loop once successful
                            except Exception as e:
                                retries += 1
                                logging.error(f"Attempt {retries}: Error sending email: {e}")
                                time.sleep(2)

                        if retries == MAX_RETRIES:
                            logging.error(f"Max retries reached for message {message['MessageId']}")
                            continue  # Move on to the next message if retries are exhausted
                    else:
                        logging.warning(f"Unsupported event type: {event_type}")

                except Exception as e:
                    logging.error(f"Unexpected error processing message: {e}")

    except Exception as e:
        logging.error(f"Error in SQS polling loop: {e}")
        time.sleep(5)

@app.route('/')
def home():
    return jsonify({"message": "Email service is running"}), 200

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "email-notification"}), 200

# Start the polling in a background thread
def start_polling():
    thread = threading.Thread(target=process_sqs)
    thread.daemon = True
    thread.start()

if __name__ == '__main__':
    start_polling()  # Start polling in the background
    app.run(host='0.0.0.0', port=5005)