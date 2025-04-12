from PyQt5.QtCore import QThread, pyqtSignal
import asyncio
from app.utils.logger import logger
from app.browser import BrowserManager
from pathlib import Path





class DownloadTask(QThread):
    """
    A QThread class to run the download tasks asynchronously.
    """
    finished = pyqtSignal()
    progress = pyqtSignal(int)

    def __init__(self, config, browser_manager: BrowserManager, should_report_progress: bool = False):
        super().__init__()
        self.config = config
        self.browser_manager = browser_manager
        self.should_report_progress = should_report_progress

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.start_download())
            self.finished.emit()
        except Exception as e:
            logger.error(f"Download task failed: {e}")
            self.finished.emit()
        finally:
            loop.close()

    async def start_download(self):
        """
        The actual download logic.
        """
        mode = self.config['mode']
        url = self.config['url']
        format_type = self.config["format_type"]
        output_dir = self.config["output_dir"]
        logger.info(f"配置: \n {self.config}")

        # Open the browser within the thread
        is_success = await self.browser_manager.open_browser()
        if is_success:
            logger.info("浏览器打开成功...")
        else:
            logger.info("打开失败...")
            return


        progress_callback = None
        if self.should_report_progress:
            logger.info("设置进度条回调")
            progress_callback = self.progress.emit


        try:
            if mode == '文章':
                # 下载合集
                await self.browser_manager.download_one(url=url, output_dir=output_dir, format_type=format_type)

            elif mode == '合集':
                article_info = await self.browser_manager.parse_album(url=url)

                total = article_info['total']
                articles = article_info['articles']
                album_name = article_info['album_name']

                output_dir = Path(output_dir) / Path(album_name)

                for i, article in enumerate(articles):
                    await self.browser_manager.download_one(url=article['link'], output_dir=output_dir, format_type=format_type)
                    if progress_callback:
                        progress = int((i + 1) / total * 10000)
                        logger.info(f"更新进度条: {progress}")
                        progress_callback(progress)

                # await self.browser_manager.download_album(url=url, output_dir=output_dir, format_type=format_type, progress_callback=progress_callback)

            elif mode == '批量':

                urls = [u.strip() for u in url.split('\n') if u.strip()]
                total = len(urls)
                for i, single_url in enumerate(urls):
                    # 这里假设批量下载不需要再解析，lineEdit中的每一行就是一个可以直接下载的URL
                    await self.browser_manager.download_one(url=single_url, output_dir=output_dir, format_type=format_type)
                    if progress_callback:
                        progress = int((i + 1) / total * 10000)
                        logger.info(f"更新进度条: {progress/100:.2f}%")  # 记录实际百分比
                        progress_callback(progress)  # 传递0-10000之间的值


        except Exception as e:
            logger.error(f"Download failed: {e}")
        finally:
            is_success = await self.browser_manager.close_browser()

            if is_success:
                logger.info("浏览器关闭成功...")
            else:
                logger.info("关闭失败...")


class ParseAlbumTask(QThread):
    articles_parsed = pyqtSignal(list, dict)  # 用于传递文章列表和配置
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, config, browser_manager: BrowserManager):
        super().__init__()
        self.config = config
        self.browser_manager = browser_manager

    def run(self):
        """
        Override the run method to execute the download task.
        """
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            article_info = loop.run_until_complete(self.parse_and_get_articles())
            if article_info:
                self.config['album_name'] = article_info['album_name']
                
                self.articles_parsed.emit(article_info['articles'], self.config)  # 发射信号
            else:
                self.error.emit("Failed to parse album.")
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))
            logger.error(f"Parse album task failed: {e}")
            self.finished.emit()
        finally:
            loop.close()

    async def parse_and_get_articles(self):
        """解析合集文章列表"""
        try:
            is_success = await self.browser_manager.open_browser()
            if not is_success:
                logger.error("Failed to open browser for parsing album.")
                return None

            article_info = await self.browser_manager.parse_album(url=self.config['url'])

            if article_info is None:
                logger.error("Failed to parse album.")
                return None

            return article_info

        except Exception as e:
            logger.error(f"解析合集失败: {e}")
            return None
        finally:
            is_success = await self.browser_manager.close_browser()
            if not is_success:
                logger.error("Failed to close browser after parsing album.")




class ArticleDownloadTask(QThread):
    """
    A QThread class to run the download tasks asynchronously.
    """
    finished = pyqtSignal()
    progress = pyqtSignal(int)

    def __init__(self, config, browser_manager: BrowserManager):
        super().__init__()
        self.config = config
        self.browser_manager = browser_manager

    def run(self):
        """
        Override the run method to execute the download task.
        """
        try:
            asyncio.run(self.start_download())
            self.finished.emit()
        except Exception as e:
            logger.error(f"Download task failed: {e}")
            self.finished.emit()

    async def start_download(self):
        """
        The actual download logic.
        """
        articles = self.config['articles']
        format_type = self.config["format_type"]
        output_dir = self.config["output_dir"]
        # album_name = self.config['album_name']
        total = self.config["total"]

        logger.info(f"配置: \n {self.config}")

        # output_dir = Path(output_dir) / Path(album_name)

        # Open the browser within the thread
        is_success = await self.browser_manager.open_browser()
        if is_success:
            logger.info("浏览器打开成功...")
        else:
            logger.info("打开失败...")
            return
        
        if not articles:
            return
        logger.info(f"当前合集名称：{output_dir}")
        logger.info(f"----------------开始下载: {len(articles)}篇文章----------------")  # Use the imported logger
        try:
            for i, article in enumerate(articles):
                url = article['link'] if isinstance(article, dict) else article
                await self.browser_manager.download_one(url=url, output_dir=output_dir, format_type=format_type)

                # 更新进度条
                logger.info(f"----------------已下载{i+1} / {len(articles)}篇文章----------------")
                progress = int((i + 1) / total * 10000)
                logger.info(f"更新进度条: {progress}")
                self.progress.emit(progress)

        except Exception as e:
            logger.error(f"Download failed: {e}")
        finally:
            is_success = await self.browser_manager.close_browser()

            if is_success:
                logger.info("浏览器关闭成功...")
            else:
                logger.info("关闭失败...")

