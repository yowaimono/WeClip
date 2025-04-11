import html2text
from pathlib import Path
from playwright.async_api import Page
from typing import Optional
from .base import ArticleExporter

class MarkdownExporter(ArticleExporter):
    def __init__(self):
        self._converter = html2text.HTML2Text()
        self._converter.ignore_links = False
    
    def get_file_extension(self) -> str:
        return ".md"
    
    async def export(self, page: Page, output_dir: Path, filename: Optional[str] = None) -> Path:
        """导出为Markdown格式"""
        await self._scroll_and_clean_page(page)
        
        filename = filename or await self._generate_filename(page)
        content_div = await page.query_selector("#page-content")
        
        if not content_div:
            raise Exception("未找到 #page-content 元素！")
        
        article_html = await content_div.inner_html()
        markdown_content = self._converter.handle(article_html)
        
        output_path = output_dir / Path(filename)
        output_path.write_text(markdown_content, encoding="utf-8")
        return output_path