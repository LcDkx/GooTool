# EasyOCR实现
import easyocr
import numpy as np
import cv2
from .base_ocr import BaseOCREngine, OCRResult
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class EasyOCREngine(BaseOCREngine):
    def __init__(self):
        self.reader = None
        self.initialized = False
    
    def initialize(self, languages: List[str] = ['ch_sim', 'en'], **kwargs) -> bool:
        """初始化EasyOCR阅读器[7,8](@ref)"""
        try:
            # 设置GPU参数，如果服务器有GPU可以设置为True
            gpu_enabled = kwargs.get('gpu', False)
            self.reader = easyocr.Reader(languages, gpu=gpu_enabled,detector=False)
            self.initialized = True
            logger.info("EasyOCR引擎初始化成功")
            return True
        except Exception as e:
            logger.error(f"EasyOCR初始化失败: {str(e)}")
            self.initialized = False
            return False
    
    def recognize_text(self, image_data, **kwargs) -> List[Dict[str, Any]]:
        """使用EasyOCR识别文字[7](@ref)"""
        if not self.initialized or not self.reader:
            raise RuntimeError("EasyOCR引擎未正确初始化")
        
        try:
            # 转换图像数据
            if isinstance(image_data, str):
                # 文件路径
                results = self.reader.readtext(image_data, **kwargs)
            elif isinstance(image_data, bytes):
                # 字节数据
                nparr = np.frombuffer(image_data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                results = self.reader.readtext(img, **kwargs)
            else:
                # 假设是numpy数组
                results = self.reader.readtext(image_data, **kwargs)
            
            # 转换为统一格式
            ocr_results = []
            for bbox, text, confidence in results:
                # 将边界框转换为标准格式
                bbox_flat = [point for coord in bbox for point in coord]
                ocr_results.append(OCRResult(text, confidence, bbox_flat).to_dict())
            
            return ocr_results
            
        except Exception as e:
            logger.error(f"EasyOCR识别失败: {str(e)}")
            raise
    
    def get_engine_info(self) -> Dict[str, Any]:
        return {
            "name": "EasyOCR",
            "version": "1.0.0",
            "languages": ["ch_sim", "en"],
            "initialized": self.initialized
        }