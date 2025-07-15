import os, asyncio
from base64 import b64decode
from datetime import timedelta
from crawl4ai import AsyncWebCrawler, CacheMode, CrawlerRunConfig
from google.cloud import storage

async def upload_to_gcs(bucket_name, destination_blob_name, data):
    """Uploads data to GCS as a file (blob)."""
    # Use the service account file explicitly
    storage_client = storage.Client.from_service_account_json("service-account.json")
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



async def main():
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        screenshot=True,
        wait_for_images=True,
        screenshot_wait_for=30,
        scan_full_page=True,
        
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://ynet.co.il",
            config=run_config
        )
        if result.success:
            print(f"Screenshot data present: {result.screenshot is not None}")

            if result.screenshot:
                print(f"[OK] Screenshot captured, size: {len(result.screenshot)} bytes")

                bucket_name = "crawl4ai-bucket"
                destination_blob_name = "screenshot.txt" 

                file_url = await upload_to_gcs(bucket_name, destination_blob_name, result.screenshot)
                print(f"[RESULT] Screenshot uploaded successfully: {file_url}")
            else:
                print("[WARN] Screenshot data is None.")

           

        else:
            print("[ERROR]", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
