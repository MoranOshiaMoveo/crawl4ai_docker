from pydantic import BaseModel, HttpUrl
from typing import Optional

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

class CrawlRequest(BaseModel):
    url: HttpUrl
    wait_for_images: Optional[bool] = True
    full_page: Optional[bool] = True
    scroll_delay: Optional[float] = 0.2
    verbose: Optional[bool] = True
    stream: Optional[bool] = False

class CrawlResponse(BaseModel):
    success: bool
    url: Optional[str] = None
    error_message: Optional[str] = None
    file_size: Optional[int] = None 