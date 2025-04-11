# from pathlib import Path
# from playwright.async_api import Page
# from typing import Optional

# from app.utils.logger import logger
# from .base import ArticleExporter
# import pdfkit
# import asyncio

# class PDFExporter(ArticleExporter):
#     def __init__(self, wkhtmltopdf_path: Optional[str] = None):
#         """初始化，可选指定 wkhtmltopdf 路径"""
#         self.wkhtmltopdf_path = wkhtmltopdf_path
    
#     def get_file_extension(self) -> str:
#         return ".pdf"
    
#     async def export(self, page: Page, output_dir: Path, filename: Optional[str] = None) -> Path:
#         """最终优化版PDF导出"""
#         await self._scroll_and_clean_page(page)
#         await page.set_extra_http_headers({'Referer': 'https://mp.weixin.qq.com/'})
        
#         filename = filename or await self._generate_filename(page)
#         output_path = output_dir / Path(filename)
        
#         # 方法1：直接使用页面HTML（简单但可能丢图）
#         # html_content = await self._get_optimized_html(page, filename)
        
#         # 方法2：下载图片后替换（推荐）
#         html_content = await self._download_images(page, output_dir)
        
#         options = {
#             'encoding': 'UTF-8',
#             'enable-local-file-access': None,
#             'images': None,
#             'javascript-delay': '2000',
#             'custom-header': [('Referer', 'https://mp.weixin.qq.com/')],
#             'no-stop-slow-scripts': None,
#         }
        
#         await self._convert_html_to_pdf(html_content, output_path, options)
#         return output_path
    
#     async def _download_images(self, page: Page, output_dir: Path) -> str:
#         """修复后的图片下载方法"""
#         img_dir = output_dir / Path("images")
#         img_dir.mkdir(exist_ok=True)
        
#         html = await page.content()
#         img_elements = await page.query_selector_all("img")
        
#         for idx, img in enumerate(img_elements):
#             try:
#                 src = await img.get_attribute("src")
#                 if not src:
#                     continue
                    
#                 # 跳过Base64图片
#                 if src.startswith('data:image'):
#                     continue
                    
#                 # 处理相对路径
#                 if src.startswith('//'):
#                     src = f'https:{src}'
#                 elif src.startswith('/'):
#                     src = f'https://mp.weixin.qq.com{src}'
                
#                 # 生成合法文件名
#                 img_ext = src.split('.')[-1].split('?')[0][:4]
#                 img_ext = img_ext if img_ext in ['jpg', 'png', 'gif', 'webp'] else 'jpg'
#                 img_name = f"image_{idx}.{img_ext}"
#                 img_path = img_dir / img_name
                
#                 # 将路径转换为 file:// URL 格式
#                 file_url = img_path.as_uri()  # 关键修改点
#                 # 使用page.context.request的正确方式
#                 request = page.context.request
#                 resp = await request.get(src)
#                 if resp.status == 200:
#                     img_data = await resp.body()
#                     img_path.write_bytes(img_data)
#                     html = html.replace(src, file_url)
#                 else:
#                     logger.warning(f"图片下载失败 HTTP {resp.status}: {src}")
                        
#             except Exception as e:
#                 logger.error(f"图片处理失败: {str(e)} | URL: {src}", exc_info=True)
        
#         return html
    

#     async def _get_optimized_html(self, page: Page, title: str) -> str:
#         """获取优化后的 HTML（添加 PDF 专用样式）"""
#         content_div = await page.query_selector("#page-content")
#         if not content_div:
#             raise Exception("未找到 #page-content 元素！")
        
#         article_html = await content_div.inner_html()
        
#         return f"""
#         <!DOCTYPE html>
#         <html>
#         <head>
#             <meta charset="UTF-8">
#             <title>{title}</title>
#             <style>
#                 body {{
#                     font-family: Arial, sans-serif;
#                     line-height: 1.6;
#                     font-size: 12pt;
#                 }}
#                 h1 {{
#                     font-size: 18pt;
#                     text-align: center;
#                     margin-bottom: 20px;
#                 }}
#                 img {{
#                     max-width: 100%;
#                     height: auto;
#                 }}
#                 pre {{
#                     background: #f5f5f5;
#                     padding: 10px;
#                     border-radius: 3px;
#                     overflow-x: auto;
#                 }}
#             </style>
#         </head>
#         <body>
#             <h1>{title}</h1>
#             {article_html}
#         </body>
#         </html>
#         """
    
#     async def _convert_html_to_pdf(self, html: str, output_path: Path, options: dict):
#         """调用 pdfkit 异步生成 PDF"""
#         loop = asyncio.get_running_loop()
        
#         # 如果指定了 wkhtmltopdf 路径，配置 pdfkit
#         config = None
#         if self.wkhtmltopdf_path:
#             config = pdfkit.configuration(wkhtmltopdf=self.wkhtmltopdf_path)
        
#         # 在后台线程中运行（避免阻塞事件循环）
#         await loop.run_in_executor(
#             None,
#             lambda: pdfkit.from_string(
#                 html,
#                 str(output_path),
#                 options=options,
#                 configuration=config
#             )
#         )