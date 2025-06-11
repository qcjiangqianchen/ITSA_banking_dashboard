# auth.py
import jwt
import json
import requests
from flask import request, jsonify
from functools import wraps


REGION = "ap-southeast-1"
USER_POOL_ID = "ap-southeast-1_ImQ6I4Ypf"
COGNITO_ISSUER = f"https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}"
JWKS_URL = f"{COGNITO_ISSUER}/.well-known/jwks.json"
CLIENT_ID = "5m07nmhkocfd7pabd5pp15flfa"

jwk_client = jwt.PyJWKClient(JWKS_URL)

# def decode_token(token):
#     try:
#         decoded = jwt.decode(
#             token,
#             options={"verify_signature": False},  # ⚠️ Only for local testing — for production, validate with public keys
#             algorithms=["RS256"]  # or "HS256" depending on your Cognito setup
#         )
#         return decoded
#     except Exception as e:
#         print("Token decoding failed:", str(e))
#         return {}


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]

        if not token:
            return jsonify({'message': 'Token is missing'}), 401    
        
        print("🔐 Token received:", token)  # <- DEBUG LINE

        try:
            signing_key = jwk_client.get_signing_key_from_jwt(token)    
            decoded_token = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=CLIENT_ID,  # or your client ID if you set one
                issuer=COGNITO_ISSUER,
                leeway=10  # ← allows for 10 seconds time skew
            )

            print("✅ Decoded token:", decoded_token)  # <- DEBUG LINE

            # Optionally: attach decoded token to request context
            request.decoded_token = decoded_token  # ✅ Attach to request

            print("🔍 Token aud claim:", decoded_token.get("aud"))
            print("🔍 Expected CLIENT_ID:", CLIENT_ID)

        except Exception as e:
            return jsonify({'message': 'Token is invalid', 'error': str(e)}), 401

        return f(*args, **kwargs)
    return decorated
