from typing import Dict, List, Any, Optional
from .base_ocr import BaseOCREngine
from .easyocr_engine import EasyOCREngine
from .baidu_ocr_engine import BaiduOCREngine
import logging

logger = logging.getLogger(__name__)

class OCRManager:
    """OCR引擎管理器，支持多种引擎动态切换"""
    
    def __init__(self):
        self.engines: Dict[str, BaseOCREngine] = {}
        self.default_engine = "baiduocr"
        self.initialized = False
    
    def register_engine(self, name: str, engine: BaseOCREngine, **kwargs) -> bool:
        """注册OCR引擎"""
        try:
            if engine.initialize(**kwargs):
                self.engines[name] = engine
                logger.info(f"OCR引擎 {name} 注册成功")
                return True
        except Exception as e:
            logger.error(f"注册OCR引擎 {name} 失败: {str(e)}")
        return False
    
    def initialize_engines(self) -> bool:
        """初始化所有引擎"""
        try:
            # 初始化EasyOCR
            # easyocr_engine = EasyOCREngine()
            # if self.register_engine("easyocr", easyocr_engine, languages=['ch_sim', 'en'], gpu=False):
            #     self.initialized = True
            #     logger.info("所有OCR引擎初始化完成")
            #     return True
            self.engines['baiduocr'] = BaiduOCREngine()
            if not self.engines['baiduocr'].initialize(languages=['ch_sim', 'en']):
                logger.error("BaiduOCR 初始化失败")
            else:
                self.default_engine = 'baiduocr'  # 设置默认引擎
                return True
        except Exception as e:
            logger.error(f"OCR引擎初始化失败: {str(e)}")
        return False
    
    def recognize_text(self, image_data, engine_name: str = None, **kwargs) -> List[Dict[str, Any]]:
        """使用指定引擎识别文字"""
        engine_name = engine_name or self.default_engine
        
        if engine_name not in self.engines:
            raise ValueError(f"不支持的OCR引擎: {engine_name}")
        
        engine = self.engines[engine_name]
        return engine.recognize_text(image_data, **kwargs)
    
    def get_available_engines(self) -> List[str]:
        """获取可用的引擎列表"""
        return list(self.engines.keys())
    
    def get_engine_info(self, engine_name: str) -> Dict[str, Any]:
        """获取引擎信息"""
        if engine_name not in self.engines:
            raise ValueError(f"引擎不存在: {engine_name}")
        return self.engines[engine_name].get_engine_info()

# 全局OCR管理器实例
ocr_manager = OCRManager()