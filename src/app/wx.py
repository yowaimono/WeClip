import asyncio
from pathlib import Path
from typing import Optional
from playwright.async_api import Page
import html2text
import os
import re
from app.export.factory import ExporterFactory
from app.utils.logger import logger

class WechatArticleDownloader:
    def __init__(self,default_format: str = "md"):
        # 默认保存格式
        self.default_format = default_format





    def _prepare_output_dir(self, output_dir=None, subfolder=None):
        """更安全的路径处理方法"""
        try:
            # 确保default_dir是Path对象
            default_dir = Path.home().joinpath("Desktop", "微信公众号文章")
            
            # 处理输入路径
            final_dir = Path(output_dir) if output_dir else default_dir
            
            # 添加子目录
            if subfolder:
                final_dir = final_dir.joinpath(str(subfolder))
            
            # 创建目录
            final_dir.mkdir(parents=True, exist_ok=True)
            
            return str(final_dir.resolve()).strip()  # 返回绝对路径
        except Exception as e:
            raise ValueError(f"创建目录失败: {e}")

    async def download_single_article(
        self, 
        page: Page, 
        url: str, 
        output_dir: Optional[str] = None,
        format_type: Optional[str] = None):
        
        """下载单篇微信公众号文章并保存为 Markdown."""
        format_type = format_type or self.default_format
        exporter = ExporterFactory.create(format_type)
        
        final_output_dir = self._prepare_output_dir(output_dir)
        logger.info(f"生成保存路径: {final_output_dir}")

        try:
            await page.goto(url, timeout=60000)
            output_path = await exporter.export(page, final_output_dir)
            logger.info(f"文章已保存为 {output_path}")
        except Exception as e:
            logger.error(f"下载文章 {url} 失败: {e}")

    async def parse_album(self, page: Page, album_url):
        """解析微信公众号合集页面（自动判断类型），提取文章链接和标题."""
        try:
            await page.goto(album_url, timeout=60000)
            logger.info("合集页面加载完成，开始解析（自动判断类型）...")
            count_element = 0
            album_name = "未命名合集"
            name_element = await page.query_selector("#js_tag_name")
            if name_element:
                album_name = (await name_element.text_content()).replace("合集：#", "").strip()
            logger.info(f"合集名称: {album_name}")

            articles = []

            # 尝试查找“展开更多”按钮，判断是否为第一种合集类型
            expand_more_button = await page.query_selector('div.unfold-more__word:has-text("展开更多")')

            if expand_more_button:
                # logger.info("检测到“展开更多”按钮，按第一种合集类型解析。")
                

                max_retries = 5
                for _ in range(max_retries):
                    try:
                        await page.wait_for_selector('div.unfold-more__word:has-text("展开更多")', timeout=5000)
                        buttons = await page.query_selector('div.unfold-more__word:has-text("展开更多")')
                        if not buttons:
                            # logger.info("已全部展开")
                            break
                        await buttons.click()
                        # logger.info("点击了一次展开更多")
                        await asyncio.sleep(1)
                    except:
                        # logger.info('已展开全部\n---THE END---')
                        break

                list_items = await page.query_selector_all(".album__list.album_novel_list li")
                for item in list_items:
                    title_element = await item.query_selector(".album__item-title-wrp")
                    title = (await title_element.text_content()).strip() if title_element else "无标题"
                    link = await item.get_attribute("data-link")
                    if link and not any(article["link"] == link for article in articles):
                        articles.append({"title": title, "link": link})

            else:
                # logger.info("未检测到“展开更多”按钮，按第二种合集类型（滚动加载）解析。")
                

                
                
                scroll_count = 0
                max_scrolls = 1000
                while scroll_count < max_scrolls:
                    await page.wait_for_selector(".album__list.js_album_list", timeout=5000)
                    list_items = await page.query_selector_all(".album__list.js_album_list li.album__list-item.js_album_item")
                    initial_article_count = len(articles)

                    for item in list_items:
                        link = await item.get_attribute("data-link")
                        title_element = await item.query_selector(".album__item-title-wrp")
                        title = (await title_element.text_content()).strip() if title_element else "无标题"
                        if link and not any(article["link"] == link for article in articles):
                            articles.append({"title": title, "link": link})

                    # logger.info(f"当前解析到 {len(articles)} 篇文章 (滚动加载)")

                    # 检测是否到达底部，判断 style="display: none;"
                    no_more_element = await page.query_selector(".over-line.js_no_more_album")
                    if no_more_element:
                        style = await no_more_element.get_attribute("style")
                        if style and "display: none;" not in style:
                            # logger.info("已到达合集底部，停止滚动。")
                            break

                    await page.evaluate("window.scrollBy(0, document.body.scrollHeight);")
                    await asyncio.sleep(1)
                    scroll_count += 1

                    if len(articles) == initial_article_count and scroll_count > 10:
                        # logger.info("多次滚动未加载更多内容，停止滚动。")
                        break

            # logger.info(f"最终解析到 {len(articles)} 篇文章")
            return {
                "album_name": album_name,
                "articles": articles,
                "total": len(articles)
            }

        except Exception as e:
            logger.error(f"解析合集 {album_url} (自动判断类型) 失败: {e}")
            return None
        
        
        
        
        
    async def download_album(self, page: Page, album_url, output_dir=None,format_type: Optional[str] = None):
        """下载微信公众号合集中的所有文章，重用传入的 page 对象."""
        album_info = await self.parse_album(page, album_url)
        logger.info(f"获取到的文章总数: {album_info['total']}")
        if album_info and album_info["articles"]:
            album_name = album_info["album_name"]
            # default_base_dir = Path.home() / "Desktop" / "微信公众号文章"
            final_dir = self._prepare_output_dir(output_dir,subfolder=album_name)
            logger.info(f"生成保存路径: {final_dir}")
            # album_output_dir = os.path.join(final_base_dir, album_name)
            os.makedirs(final_dir, exist_ok=True)
            
            # 获取保存格式
            format_type = format_type or self.default_format
            
            exporter = ExporterFactory.create(format_type=format_type)
            
            # logger.info(f"进入下载循环...,保存类型{format_type}")
            
            for index, article in enumerate(album_info["articles"]):
                logger.info(f"开始下载第 {index + 1} 篇文章: {article['title']} - {article['link']}")
                logger.info(f"已下载: {index} / {album_info['total']}")
                try:
                    await page.goto(article["link"], timeout=60000)
                    title_element = await page.query_selector(".rich_media_title")
                    if title_element:
                        title = (await title_element.text_content()).strip()
                        filename = f"{title}.{format_type}"
                        filename = re.sub(r'[\\/:*?\"<>|]', '_', filename)
                        await exporter.export(page, final_dir, filename)
                    else:
                        filename = f"{album_name} - {self._extract_title_from_url(article['link'])}.{format_type}"
                        filename = re.sub(r'[\\/:*?\"<>|]', '_', filename)
                        await exporter.export(page, final_dir, filename)
                except Exception as e:
                    logger.error(f"下载文章 {article['title']} - {article['link']} 失败: {e}")
        else:
            logger.info(f"无法解析合集或合集为空: {album_url}")

    async def batch_download(self, page: Page, urls_text, output_dir=None,format_type:Optional[str] = None):
        """批量下载微信公众号文章，urls_text 按行分割，每一行都是一个 URL."""

        final_output_dir = self._prepare_output_dir(output_dir=output_dir)

        logger.info(f"生成保存路径: {final_output_dir}")
        os.makedirs(final_output_dir, exist_ok=True)

        urls = urls_text.strip().split('\n')
        logger.info(f"分割成{len(urls)}个url...")
        # urls = [url.strip() for url in urls if url.strip() and (url.startswith('http://') or url.startswith('https://'))]
        logger.info(f"解析到 {len(urls)} 个 URL，开始下载到 {final_output_dir}...")
        for url in urls:
            logger.info(f"开始下载: {url}")
            await self.download_single_article(page, url, final_output_dir,format_type=format_type)
        logger.info("批量下载完成。")

    def _extract_title_from_url(self, url):
        """简单地从 URL 中提取可能作为标题的片段."""
        parts = url.split('/')
        if parts and parts[-1]:
            return parts[-1].split('.')[0]
        return "未命名文章"