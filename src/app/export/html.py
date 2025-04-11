from pathlib import Path
from playwright.async_api import Page
from typing import Optional
from .base import ArticleExporter
from app.utils.logger import logger
class HTMLExporter(ArticleExporter):
    
    def get_file_extension(self) -> str:
        return ".html"
    
    async def export(self, page: Page, output_dir: Path, filename: Optional[str] = None) -> Path:
        """导出为HTML格式"""
        await self._scroll_and_clean_page(page)
        
        file_extension = self.get_file_extension()
        
        logger.info(f"目标文件扩展名： {file_extension}")
        
        filename = filename or await self._generate_filename(page)
        logger.info(f"生成文件名...{filename}")
        content_div = await page.query_selector("#page-content")
        
        if not content_div:
            raise Exception("未找到 #page-content 元素！")
        
        article_html = await content_div.inner_html()
        styled_html = self._wrap_html(article_html, filename)
        
        output_path = output_dir / Path(filename)
        output_path.write_text(styled_html, encoding="utf-8")
        return output_path
    
    def _wrap_html(self, content: str, title: str) -> str:
        """包装HTML内容，添加样式和结构"""
        return f"""<!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="UTF-8">
                        <title>{title}</title>
                        <style>
                            body {{ max-width: 800px; margin: 0 auto; padding: 20px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; }}
                            img {{ max-width: 100%; height: auto; }}
                            h1 {{ font-size: 1.8em; border-bottom: 1px solid #eee; }}
                            pre {{ background: #f5f5f5; padding: 10px; border-radius: 3px; overflow-x: auto; }}
                            blockquote {{ border-left: 4px solid #ddd; padding-left: 15px; color: #777; }}
                        </style>
                    </head>
                    <body>
                        {content}
                    </body>
                    </html>"""