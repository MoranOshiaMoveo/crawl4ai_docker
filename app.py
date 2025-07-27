
from fastapi import FastAPI
from models import ScreenshotRequest, ScreenshotResponse, CrawlRequest, CrawlResponse
import uvicorn

from controllers.crawl import get_crawl
from controllers.screenshot import get_screenshot

app = FastAPI(
    title="Crawl4AI Screenshot Service",
    description="A FastAPI service for taking website screenshots and uploading to Google Cloud Storage",
    version="1.0.0"
)

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
    return await get_screenshot(request)

@app.post("/crawl")
async def crawl(request: CrawlRequest):
    return await get_crawl(request)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 