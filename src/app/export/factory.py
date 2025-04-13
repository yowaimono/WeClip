from typing import Dict, Optional, Type
from .base import ArticleExporter
from .md import MarkdownExporter
from .html import HTMLExporter
from .pdf import PDFExporter
from app.utils.logger import logger
class ExporterFactory:
    """导出器工厂，管理各种导出格式"""
    
    _exporters: Dict[str, Type[ArticleExporter]] = {
        "md": MarkdownExporter,
        "markdown": MarkdownExporter,
        "html": HTMLExporter,
        "pdf": PDFExporter,
    }
    
    @classmethod
    def create(cls, format_type: str) -> ArticleExporter:
        """创建指定类型的导出器"""
        logger.info(f"类型：{format_type.lower()}")
        exporter_class = cls._exporters.get(format_type.lower())
        if not exporter_class:
            raise ValueError(f"不支持的导出格式: {format_type}")
        return exporter_class()
    
    @classmethod
    def register_format(cls, format_type: str, exporter_class: Type[ArticleExporter]):
        """注册新的导出格式"""
        if not issubclass(exporter_class, ArticleExporter):
            raise TypeError("导出器必须继承自ArticleExporter")
        cls._exporters[format_type.lower()] = exporter_class
    
    @classmethod
    def supported_formats(cls) -> list:
        """获取支持的导出格式列表"""
        return list(cls._exporters.keys())