########################## testing s3 bucket 

# import boto3
# import os
# from dotenv import load_dotenv

# # Load environment variables from .env file
# load_dotenv()

# def test_s3_access():
#     # Get credentials from environment variables
#     aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
#     aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
#     aws_region = os.getenv('AWS_REGION')
#     bucket_name = os.getenv('LOGGING_BUCKET_NAME')
    
#     # Confirm environment variables were loaded
#     if not all([aws_access_key_id, aws_secret_access_key, aws_region, bucket_name]):
#         print("❌ Missing required environment variables")
#         return False
    
#     # Create S3 client with credentials from .env
#     s3 = boto3.client(
#         's3',
#         region_name=aws_region,
#         aws_access_key_id=aws_access_key_id,
#         aws_secret_access_key=aws_secret_access_key
#     )
    
#     try:
#         # Check if bucket exists
#         s3.head_bucket(Bucket=bucket_name)
#         print("✅ S3 bucket exists and is accessible")
        
#         # Test writing a sample object
#         s3.put_object(
#             Bucket=bucket_name,
#             Key='test/test-object.json',
#             Body='{"test": "successful"}',
#             ContentType='application/json'
#         )
#         print("✅ Successfully wrote to S3 bucket")
        
#         # Test reading the object
#         response = s3.get_object(
#             Bucket=bucket_name,
#             Key='test/test-object.json'
#         )
#         content = response['Body'].read().decode('utf-8')
#         print(f"✅ Successfully read from S3 bucket: {content}")
        
#         return True
#     except Exception as e:
#         print(f"❌ S3 test failed: {e}")
#         return False

# if __name__ == "__main__":
#     test_s3_access()


############################## testing logging_service.py

# import requests
# import json
# import os
# from dotenv import load_dotenv

# # Load environment variables from .env file
# load_dotenv()

# def test_logging_service():
#     # Get service URL from environment variable or use default
#     # You'll need to add SERVICE_URL to your .env file
#     base_url = os.getenv('SERVICE_URL', 'http://localhost:5001')
    
#     print(f"🔍 Testing logging service at: {base_url}")
    
#     # Test creating a log
#     create_data = {
#         "operation": "CREATE",
#         "agent_id": "test-agent-123",
#         "client_id": "test-client-456",
#     }
    
#     try:
#         # Test API connectivity first
#         health_check = requests.get(f"{base_url}/health", timeout=5)
#         if health_check.status_code == 200:
#             print("✅ Service health check passed")
#         else:
#             print(f"⚠️ Service health check returned: {health_check.status_code}")
#     except requests.exceptions.RequestException as e:
#         print(f"❌ Cannot connect to service: {e}")
#         print("Make sure the service is running and the URL is correct")
#         return False
        
#     try:
#         response = requests.post(
#             f"{base_url}/api/logs",
#             json=create_data,
#             timeout=10  # Add timeout to prevent hanging
#         )
        
#         if response.status_code == 201:
#             result = response.json()
#             log_id = result.get('log_id')
#             print(f"✅ Log created successfully: {log_id}")
            
#             # Test retrieving logs for a client
#             get_response = requests.get(
#                 f"{base_url}/api/logs/test-client-456?agent_id=test-agent-123",
#                 timeout=10
#             )
            
#             if get_response.status_code == 200:
#                 logs = get_response.json()
#                 print(f"✅ Retrieved logs for client: {len(logs.get('logs', []))} logs found")
#                 return True
#             else:
#                 print(f"❌ Failed to retrieve logs: {get_response.status_code}")
#                 print(f"Response: {get_response.text}")
#                 return False
#         else:
#             print(f"❌ Failed to create log: {response.status_code}")
#             print(f"Response: {response.text}")
#             return False
#     except requests.exceptions.Timeout:
#         print("❌ Request timed out - service may be slow or unresponsive")
#         return False
#     except requests.exceptions.ConnectionError:
#         print("❌ Connection error - check if the service is running and network connectivity")
#         return False
#     except Exception as e:
#         print(f"❌ Error testing logging service: {e}")
#         return False

# if __name__ == "__main__":
#     test_logging_service()
    
