from typing import Optional
from playwright.async_api import async_playwright
from app.utils.logger import logger
from app.wx import WechatArticleDownloader


class BrowserManager:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
        self.downloader = WechatArticleDownloader()

    async def open_browser(self):
        """使用 Playwright 异步 API 打开浏览器实例并创建页面."""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)  # 默认使用 Chromium
            self.page = await self.browser.new_page()
            # await self.page.goto("https://www.bing.com/")
            return True
        except Exception as e:
            logger.info(f"使用 Playwright 异步 API 打开浏览器失败: {e}")
            return False

    async def close_browser(self):
        """关闭当前 Playwright 浏览器实例和上下文."""
        if self.page:
            try:
                await self.page.close()
                self.page = None
            except Exception as e:
                logger.info(f"关闭 Playwright 页面失败: {e}")
                return False
        if self.browser:
            try:
                await self.browser.close()
                self.browser = None
            except Exception as e:
                logger.info(f"关闭 Playwright 浏览器失败: {e}")
                return False
        if self.playwright:
            try:
                await self.playwright.stop()
                self.playwright = None
            except Exception as e:
                logger.info(f"停止 Playwright 失败: {e}")
                return False
        return True

    async def download_one(self, url: str, output_dir: Optional[str] = None, format_type: Optional[str] = None):
        try:
            await self.downloader.download_single_article(page=self.page, url=url, output_dir=output_dir,
                                                           format_type=format_type)
            logger.info(f"下载文章完成：{url}")
        except Exception as e:
            logger.error(f"下载文章失败：{e}")

    async def download_album(self, url: str, output_dir: str = None, format_type: Optional[str] = None):
        try:
            await self.downloader.download_album(page=self.page, album_url=url, output_dir=output_dir,
                                                  format_type=format_type)
            logger.info(f"下载合集完成：{url}")
        except Exception as e:
            logger.error(f"下载合集失败：{e}")

    async def batch_download(self, urls, output_dir=None, format_type: Optional[str] = None):
        try:
            await self.downloader.batch_download(page=self.page, urls_text=urls, output_dir=output_dir,
                                                  format_type=format_type)

            logger.info(f"批量下载完成：{urls}")
        except Exception as e:
            logger.error(f"批量下载失败：{e}")
