from crawl4ai import CrawlerRunConfig, CacheMode
from models import ScreenshotRequest, ScreenshotResponse
from utils import create_json_file, upload_to_gcs
from crawl4ai import AsyncWebCrawler
import time

async def get_screenshot(request: ScreenshotRequest):
    try:
        print("🔑 Testing service account credentials...")
        create_json_file()

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
                
                url_clean = str(request.url).replace("://", "_").replace("/", "_").replace(".", "_")
                timestamp = int(time.time())
                destination_blob_name = f"screenshots/{url_clean}_{timestamp}.txt"
                
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
    