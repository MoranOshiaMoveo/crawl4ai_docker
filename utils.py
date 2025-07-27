import os
import json
import google.auth
from google.auth.transport.requests import Request
from google.cloud import storage
from datetime import timedelta

def create_json_file():
    # Get private key and fix formatting - this is crucial for PEM parsing
    private_key = os.getenv("PRIVATE_KEY")
    if private_key:
        # Replace literal \n with actual newlines - this fixes the PEM parsing error
        private_key = private_key.replace("\\n", "\n")
        print(f"✅ Converted {private_key.count(chr(10))} literal \\n to newlines")
    
    bucket_info = {
        "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_X509_CERT_URL"),
        "auth_uri": os.getenv("AUTH_URI"),
        "client_email": os.getenv("CLIENT_EMAIL"),
        "client_id": os.getenv("CLIENT_ID"),
        "client_x509_cert_url": os.getenv("CLIENT_X509_CERT_URL"),
        "private_key": private_key,  # Use the formatted private key
        "private_key_id": os.getenv("PRIVATE_KEY_ID"),
        "project_id": os.getenv("PROJECT_ID"),
        "token_uri": os.getenv("TOKEN_URI"),
        "type": os.getenv("TYPE"),
        "universe_domain": os.getenv("UNIVERSE_DOMAIN")
    }
    
    with open("service-account.json", "w") as f:
        json.dump(bucket_info, f, indent=2)
    
    print("✅ Service account JSON created with properly formatted private key")
  
    
async def upload_to_gcs(bucket_name, destination_blob_name, data):
    """Uploads data to GCS as a file (blob)."""
    try:
        print("🔑 Testing service account credentials...")
        storage_client = storage.Client.from_service_account_json("service-account.json")
        bucket = storage_client.bucket(bucket_name)
        bucket_info = bucket.reload()
        print(f"✅ Successfully accessed bucket: {bucket_name}")
        
    except Exception as e:
        print(f"❌ Credential test failed: {e}")
        raise Exception(f"Service account authentication failed: {e}")
    
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_string(data)
    
    signed_url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(hours=24),
        method="GET"
    )
    
    return signed_url
