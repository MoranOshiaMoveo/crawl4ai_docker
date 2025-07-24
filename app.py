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
from google.cloud.iam_credentials_v1 import IAMCredentialsClient
from datetime import timedelta
from fastapi import HTTPException  # or your framework’s equivalent

async def upload_to_gcs(bucket_name: str, destination_blob_name: str, data: str) -> str:
    """Uploads data to GCS as a file (blob) and returns a V4 signed URL (1h)."""
    try:
        # 1) Grab default credentials (Cloud Run service account) + project
        credentials, project_id = google.auth.default()
        # refresh to populate service_account_email
        credentials.refresh(Request())

        # 2) Prepare an IAM Credentials client to sign blobs
        iam_client = IAMCredentialsClient()
        sa_email = credentials.service_account_email

        def iam_signer(bytes_to_sign: bytes) -> bytes:
            resp = iam_client.sign_blob(
                request={
                    "name": f"projects/-/serviceAccounts/{sa_email}",
                    "payload": bytes_to_sign,
                }
            )
            return resp.signed_blob

        # 3) Use the same credentials for Storage client
        storage_client = storage.Client(credentials=credentials, project=project_id)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)

        # 4) Upload the data
        blob.upload_from_string(data)

        # 5) Generate the signed URL using our IAM-based signer
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(hours=1),
            method="GET",
            service_account_email=sa_email,
            signer=iam_signer,
        )

        print(f"[OK] Uploaded to gs://{bucket_name}/{destination_blob_name}")
        return signed_url

    except Exception as e:
        print(f"[ERROR] Failed to upload to GCS: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload to GCS: {e}")

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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 