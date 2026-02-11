from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

PROFILE_DIR = os.getenv("PLAYWRIGHT_PROFILE_DIR")
CHROME_PATH = os.getenv("CHROME_PATH")


class BrowserManager:

    def __init__(
        self,
        headless: bool = False,
        user_data_dir: Optional[str] = PROFILE_DIR,
        chrome_path: Optional[str] = CHROME_PATH,
    ):
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.chrome_path = chrome_path

        self.playwright = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        self.browser: Optional[Browser] = None


    def start(self):
       
        if self.playwright is not None:
            return  

        self.playwright = sync_playwright().start()

        if self.user_data_dir:
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                executable_path=self.chrome_path,
                headless=self.headless,
                viewport={"width": 1280, "height": 800},
                ignore_https_errors=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                ],
            )

        else:

            self.browser = self.playwright.chromium.launch(
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled"],
            )
            self.context = self.browser.new_context(
                viewport={"width": 1280, "height": 800},
                ignore_https_errors=True,
            )


        self.page = self.context.new_page()

    def get_page(self) -> Page:
        
        if self.page is None:
            raise RuntimeError("BrowserManager not started. Call start() first.")
        return self.page

    def close(self):
        if self.context:
            self.context.close()

        if self.browser:
            self.browser.close()

        if self.playwright:
            self.playwright.stop()

        self.playwright = None
        self.context = None
        self.page = None

