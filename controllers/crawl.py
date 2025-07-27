import asyncio
from crawl4ai import BrowserConfig, CrawlerRunConfig, CacheMode, LXMLWebScrapingStrategy
from crawl4ai import AsyncWebCrawler
from models import CrawlRequest, CrawlResponse
import time
from utils import create_json_file, upload_to_gcs

async def get_crawl(request: CrawlRequest):
    create_json_file()
    browser_config = BrowserConfig(headless=True)
    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS, 
        wait_for_images= request.wait_for_images,
        scan_full_page= request.full_page,
        scroll_delay= request.scroll_delay,
        verbose= request.verbose,
        scraping_strategy= LXMLWebScrapingStrategy(),
        stream= request.stream
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url=str(request.url), config=crawler_config
        )
        html = result.html
        if html:
            print(f"[OK] Screenshot captured for {request.url}")
                    
            url_clean = str(request.url).replace("://", "_").replace("/", "_").replace(".", "_")
            timestamp = int(time.time())
            destination_blob_name = f"htmls/{url_clean}_{timestamp}.html"
            
            bucket_name = "crawl4ai-bucket"
            
            signed_url = await upload_to_gcs(bucket_name, destination_blob_name, html)
            
            return CrawlResponse(
                success=True,
                url=signed_url,
                file_size=len(html)
            )
        else:
            error_msg = result.error_message if result.error_message else "Crawl failed"
            return CrawlResponse(
                success=False,
                error_message=error_msg
            )
