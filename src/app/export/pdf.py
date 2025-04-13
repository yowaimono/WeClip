from pathlib import Path
from typing import Optional

from app.export.base import ArticleExporter
from app.utils.logger import logger


class PDFExporter(ArticleExporter):
    """PDF导出器"""

    async def export(self, page, output_dir: Path, filename: Optional[str] = None) -> Path:
        """将文章内容导出为PDF文件"""
        await self._scroll_and_clean_page(page)  

        if not filename:
            filename = await self._generate_filename(page)

        filepath = output_dir / Path(filename)
        logger.info(f"PDF导出路径: {filepath}")

        await page.pdf(path=str(filepath))  # Save the page as PDF

        return filepath

    def get_file_extension(self) -> str:
        """返回PDF文件扩展名"""
        return ".pdf"