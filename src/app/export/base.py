from abc import ABC, abstractmethod
from pathlib import Path
from playwright.async_api import Page
from typing import Optional
import re
from app.utils.logger import logger


class ArticleExporter(ABC):
    """文章导出器抽象基类"""
    
    @abstractmethod
    async def export(self, page: Page, output_dir: Path, filename: Optional[str] = None) -> Path:
        """将文章内容导出到指定格式的文件"""
        pass

    @abstractmethod
    def get_file_extension(self) -> str:
        """返回文件扩展名"""
        pass

    async def _scroll_and_clean_page(self, page: Page):
        """滚动页面并清理元素(公共实现)"""
        await page.evaluate("""async () => {
            await new Promise((resolve) => {
                let scrollHeight = document.body.scrollHeight;
                let currentPosition = 0;
                const distance = 100;
                const timer = setInterval(() => {
                    window.scrollBy(0, distance);
                    currentPosition += distance;
                    if (currentPosition >= scrollHeight) {
                        clearInterval(timer);
                        resolve();
                    }
                }, 100);
            });
        }""")
        
        await page.evaluate("""() => {
            const selectors = ["#content_bottom_area", "#content_bottom_interaction"];
            selectors.forEach(selector => {
                const element = document.querySelector(selector);
                if (element) element.remove();
            });
        }""")

    async def _generate_filename(self, page: Page) -> str:
        """生成文件名(公共实现)"""
        file_extension  = self.get_file_extension()
        logger.info(f"实际文件扩展名：{file_extension}")
        title_element = await page.query_selector(".rich_media_title")
        if title_element:
            title = (await title_element.text_content()).strip()
            return self._sanitize_filename(title) + self.get_file_extension()
        
        return self._extract_title_from_url(page.url) + self.get_file_extension()

    def _extract_title_from_url(self, url: str) -> str:
        """从URL提取标题"""
        parts = url.split('/')
        if parts and parts[-1]:
            return parts[-1].split('.')[0]
        return "未命名文章"

    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名中的非法字符"""
        return re.sub(r'[\\/:*?\"<>|]', '_', filename)