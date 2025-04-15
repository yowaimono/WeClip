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
    
    # async def export(self, page: Page, output_dir: Path, filename: Optional[str] = None) -> Path:
    #     """导出为Markdown格式"""
    #     await self._scroll_and_clean_page(page)
        
    #     filename = filename or await self._generate_filename(page)
    #     content_div = await page.query_selector("#page-content")
    #     # content_div = page.content
        
    #     if not content_div:
    #         raise Exception("未找到 #page-content 元素！")
        
    #     article_html = await content_div.inner_html()
    #     markdown_content = self._converter.handle(article_html)

        
    #     output_path = output_dir / Path(filename)
    #     output_path.write_text(markdown_content, encoding="utf-8")
    #     return output_path
    
    async def export(self, page: Page, output_dir: Path, filename: Optional[str] = None) -> Path:
        """导出为Markdown格式"""
        await self._scroll_and_clean_page(page)
        
        
        await page.evaluate("""() => {
            // 要移除的元素列表
            const selectors = [
                "#meta_content",  // 原 meta_content
                "#js_article_bottom_bar",  // 底部栏
                ".wx_profile_card_inner",  // 微信名片
                "#js_a11y_wx_profile_logo",  // 微信 logo
                ".rich_media_tool_area",  // 工具栏
                "#content_bottom_area",  // 原内容底部区域
                "#content_bottom_interaction"  // 原交互区域
            ];
            
            selectors.forEach(selector => {
                const element = document.querySelector(selector);
                if (element) element.remove();
            });
        }""")
        

        filename = filename or await self._generate_filename(page)
        # 获取整个页面的 HTML 内容
        article_html = await page.content()

        # 移除不需要的元素
        # (This part is already handled in _scroll_and_clean_page, so no need to repeat it here)

        markdown_content = self._converter.handle(article_html)
        
        # 最终处理
        # 找到含有 “预览时标签不可点” 的一行，把这行后面的内容砍掉
        try:
            index = markdown_content.index("预览时标签不可点")
            markdown_content = markdown_content[:index]
        except ValueError:
            # If the string is not found, keep the entire content
            pass

        output_path = output_dir / Path(filename)
        output_path.write_text(markdown_content, encoding="utf-8")
        return output_path