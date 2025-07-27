import json
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Optional
import asyncio
from base64 import b64decode
from datetime import timedelta
from crawl4ai import AsyncWebCrawler, CacheMode, CrawlerRunConfig
import uvicorn
import google.auth
import google.auth.transport.requests
from google.cloud import storage

app = FastAPI(
    title="Crawl4AI Screenshot Service",
    description="A FastAPI service for taking website screenshots and uploading to Google Cloud Storage",
    version="1.0.0"
)

class ScreenshotRequest(BaseModel):
    url: HttpUrl
    screenshot_wait_for: Optional[int] = 30
    full_page: Optional[bool] = True
    wait_for_images: Optional[bool] = True

class ScreenshotResponse(BaseModel):
    success: bool
    url: Optional[str] = None
    error_message: Optional[str] = None
    file_size: Optional[int] = None

import google.auth
from google.auth.transport.requests import Request
from google.cloud import storage
from datetime import timedelta

async def upload_to_gcs(bucket_name, destination_blob_name, data):
    """Uploads data to GCS as a file (blob)."""
    try:
        # Test the service account credentials first
        print("🔑 Testing service account credentials...")
        storage_client = storage.Client.from_service_account_json("service-account.json")
        
        # Simple test: try to get the project info
        project_id = storage_client.project
        print(f"✅ Successfully authenticated with project: {project_id}")
        
        # Test bucket access
        print(f"🪣 Testing access to bucket: {bucket_name}")
        bucket = storage_client.bucket(bucket_name)
        
        # Try to get bucket metadata (this will fail if no access)
        bucket_info = bucket.reload()
        print(f"✅ Successfully accessed bucket: {bucket_name}")
        
    except Exception as e:
        print(f"❌ Credential test failed: {e}")
        raise Exception(f"Service account authentication failed: {e}")
    
    # If we get here, credentials are working
    print("🚀 Proceeding with file upload...")
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_string(data)
    
    # Generate a signed URL for temporary access (valid for 1 hour)
    signed_url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(hours=1),
        method="GET"
    )
    
    print(f"[OK] Uploaded to gs://{bucket_name}/{destination_blob_name}")
    print(f"[URL] File available at: {signed_url}")
    print(f"[INFO] Signed URL valid for 1 hour")
    
    return signed_url
@app.get("/")
async def root():
    return {"message": "Crawl4AI Screenshot Service is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "crawl4ai-screenshot"}

@app.post("/screenshot", response_model=ScreenshotResponse)
async def take_screenshot(request: ScreenshotRequest):
    """
    Take a screenshot of the specified URL and upload it to Google Cloud Storage.
    Returns a signed URL for accessing the screenshot.
    """
    try:
        run_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            screenshot=True,
            wait_for_images=request.wait_for_images,
            screenshot_wait_for=request.screenshot_wait_for,
            scan_full_page=request.full_page,
        )

        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(
                url=str(request.url),
                config=run_config
            )
            
            if result.success and result.screenshot:
                print(f"[OK] Screenshot captured for {request.url}, size: {len(result.screenshot)} bytes")
                
                import time
                url_clean = str(request.url).replace("://", "_").replace("/", "_").replace(".", "_")
                timestamp = int(time.time())
                destination_blob_name = f"screenshots/{url_clean}_{timestamp}.png"
                
                bucket_name = "crawl4ai-bucket"
                
                signed_url = await upload_to_gcs(bucket_name, destination_blob_name, result.screenshot)
                
                return ScreenshotResponse(
                    success=True,
                    url=signed_url,
                    file_size=len(result.screenshot)
                )
            else:
                error_msg = result.error_message if result.error_message else "Screenshot capture failed"
                return ScreenshotResponse(
                    success=False,
                    error_message=error_msg
                )
                
    except Exception as e:
        print(f"[ERROR] Exception in take_screenshot: {e}")
        return ScreenshotResponse(
            success=False,
            error_message=str(e)
        )
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
    
    # Debug: Show the structure without exposing sensitive data
    debug_info = {k: f"<{len(str(v))} chars>" if k == "private_key" else v for k, v in bucket_info.items()}
    print(f"📋 Service Account Structure: {debug_info}")
    
    # Verify the JSON can be read back
    try:
        with open("service-account.json", "r") as f:
            test_data = json.load(f)
        print("✅ Service account JSON is valid and readable")
        return True
    except Exception as e:
        print(f"❌ Error reading service account JSON: {e}")
        return False
        
if __name__ == "__main__":
    print("🎉 Starting FastAPI server...")
    print("🔑 Testing service account credentials...")
    create_json_file()
    print("🚀 Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000) 