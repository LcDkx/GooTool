# OCR实现基类
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import base64
from PIL import Image
import io

class BaseOCREngine(ABC):
    """OCR引擎基类，定义统一接口"""
    
    @abstractmethod
    def initialize(self, **kwargs) -> bool:
        """初始化OCR引擎"""
        pass
    
    @abstractmethod
    def recognize_text(self, image_data, **kwargs) -> List[Dict[str, Any]]:
        """识别图片中的文字"""
        pass
    
    @abstractmethod
    def get_engine_info(self) -> Dict[str, Any]:
        """获取引擎信息"""
        pass

class OCRResult:
    """统一OCR结果格式"""
    def __init__(self, text: str, confidence: float = 0.0, bbox: Optional[List] = None):
        self.text = text
        self.confidence = confidence
        self.bbox = bbox  # 边界框坐标 [x1, y1, x2, y2]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "confidence": self.confidence,
            "bbox": self.bbox
        }