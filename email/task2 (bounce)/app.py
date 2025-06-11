from flask import Flask
import json
import boto3
import threading
import time
import os

app = Flask(__name__)

# Configuration
SQS_QUEUE_URL = os.getenv('SQS_QUEUE_URL')
STAFF_EMAIL = os.getenv('STAFF_EMAIL', 'itsateam3@gmail.com')

# AWS clients
ses = boto3.client('ses', region_name='ap-southeast-1')
sqs = boto3.client('sqs', region_name='ap-southeast-1')

def poll_sqs_and_process():
    while True:
        try:
            response = sqs.receive_message(
                QueueUrl=SQS_QUEUE_URL,
                AttributeNames=['All'],
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20
            )

            if 'Messages' in response:
                for message in response['Messages']:
                    try:
                        bounce_message = message['Body']
                        process_bounce_notification(bounce_message)

                        receipt_handle = message['ReceiptHandle']
                        sqs.delete_message(
                            QueueUrl=SQS_QUEUE_URL,
                            ReceiptHandle=receipt_handle
                        )
                    except Exception as e:
                        print(f"Error processing message: {e}")
            else:
                print("No messages received from SQS.")

            time.sleep(5)
        except Exception as e:
            print(f"Error polling SQS: {e}")
            time.sleep(5)

def process_bounce_notification(bounce_message):
    try:
        sns_message = json.loads(bounce_message)
        bounce_details = json.loads(sns_message['Message'])

        if 'bounce' in bounce_details:
            bounce_type = bounce_details['bounce']['bounceType']
            message_id = bounce_details['mail']['messageId']
            bounced_recipients = bounce_details['bounce']['bouncedRecipients']

            subject = f"Bounce Notification for Message ID: {message_id}"
            body = "The following recipients failed to receive the email:\n\n"

            for recipient in bounced_recipients:
                body += f"Recipient: {recipient['emailAddress']}\n"
                body += f"Status: {recipient['status']}\n"
                body += f"Bounce Type: {bounce_type}\n\n"

            send_bounce_to_staff(STAFF_EMAIL, subject, body)
        else:
            print("No 'bounce' key found in the message.")
    except Exception as e:
        print(f"Error processing bounce notification: {e}")

def send_bounce_to_staff(recipient, subject, body):
    try:
        response = ses.send_email(
            Source=STAFF_EMAIL,
            Destination={'ToAddresses': [recipient]},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Text': {'Data': body}},
            }
        )
        print(f"Bounce notification sent to staff: {recipient}")
    except Exception as e:
        print(f"Failed to send bounce notification: {e}")

# Start polling thread
def start_polling():
    thread = threading.Thread(target=poll_sqs_and_process)
    thread.daemon = True
    thread.start()

@app.route('/')
def home():
    return "Bounce email listener is running."

# Run on port 5006
if __name__ == '__main__':
    start_polling()  # Start polling in the background
    app.run(host='0.0.0.0', port=5006)
