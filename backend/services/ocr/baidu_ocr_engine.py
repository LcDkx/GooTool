# 百度ocr实现
# BaiduOCR实现
import requests
import base64
import time
import numpy as np
import cv2
from PIL import Image
import io
import os
from .base_ocr import BaseOCREngine, OCRResult
from typing import List, Dict, Any
import logging
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(".env")

logger = logging.getLogger(__name__)

class BaiduOCREngine(BaseOCREngine):
    def __init__(self):
        self.access_token = None
        self.token_expire_time = 0
        self.api_key = None
        self.secret_key = None
        self.language_type = 'CHN_ENG'  # 默认
        self.initialized = False
    
    def initialize(self, languages: List[str] = ['ch_sim', 'en'], **kwargs) -> bool:
        """初始化BaiduOCR，需要API Key和Secret Key（从环境变量获取）"""
        self.api_key = os.getenv('BAIDU_OCR_API_KEY') or kwargs.get('api_key')
        self.secret_key = os.getenv('BAIDU_OCR_SECRET_KEY') or kwargs.get('secret_key')
        
        if not self.api_key or not self.secret_key:
            logger.error("BaiduOCR初始化失败: 缺少 BAIDU_OCR_API_KEY 或 BAIDU_OCR_SECRET_KEY 环境变量")
            return False
        
        # 映射语言
        if 'ch_sim' in languages and 'en' in languages:
            self.language_type = 'CHN_ENG'
        elif 'en' in languages:
            self.language_type = 'ENG'
        else:
            self.language_type = 'CHN_ENG'  # 默认中英混合
        
        if self._get_access_token():
            self.initialized = True
            logger.info("BaiduOCR引擎初始化成功")
            return True
        else:
            logger.error("BaiduOCR初始化失败: 获取 access_token 失败")
            return False
    
    def _get_access_token(self) -> bool:
        """获取或刷新 access_token"""
        if time.time() < self.token_expire_time:
            return True
        
        token_url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={self.api_key}&client_secret={self.secret_key}"
        response = requests.post(token_url)
        
        if response.status_code == 200:
            data = response.json()
            if 'access_token' in data:
                self.access_token = data['access_token']
                self.token_expire_time = time.time() + data['expires_in'] - 60  # 提前1分钟刷新
                return True
        logger.error(f"获取 access_token 失败: {response.text}")
        return False
    
    def recognize_text(self, image_data, **kwargs) -> List[Dict[str, Any]]:
        """使用BaiduOCR识别文字"""
        if not self.initialized:
            raise RuntimeError("BaiduOCR引擎未正确初始化")
        
        if not self._get_access_token():
            raise RuntimeError("Access token 获取失败")
        
        try:
            # 转换图像数据为 base64
            if isinstance(image_data, str):  # 文件路径
                with open(image_data, 'rb') as f:
                    img_bytes = f.read()
            elif isinstance(image_data, bytes):  # 字节数据
                img_bytes = image_data
            else:  # 假设是numpy数组
                img = cv2.cvtColor(image_data, cv2.COLOR_BGR2RGB) if len(image_data.shape) == 3 else image_data
                pil_img = Image.fromarray(img)
                buf = io.BytesIO()
                pil_img.save(buf, format='PNG')
                img_bytes = buf.getvalue()
            
            base64_image = base64.b64encode(img_bytes).decode('utf-8')
            # print("0000000000000")
            # API 请求（使用高精度版以获取置信度和边界框）
            ocr_url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic?access_token={self.access_token}"
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            data = {
                'image': base64_image,
                'language_type': self.language_type,
                'detect_direction': 'true',  # 可选：检测方向
                'probability': 'true'  # 启用置信度
            }
            
            response = requests.post(ocr_url, headers=headers, data=data)
            if response.status_code != 200:
                raise ValueError(f"BaiduOCR HTTP错误: {response.status_code} - {response.text}")
            # print("1111111111111")
            result = response.json()
            if 'error_code' in result:
                raise ValueError(f"BaiduOCR API错误: {result.get('error_msg', '未知错误')}")
            
            # 转换为统一格式
            ocr_results = []
            for item in result.get('words_result', []):
                text = item.get('words', '')
                confidence = item.get('probability', {}).get('average', 0.0)
                loc = item.get('location', {})
                left, top, width, height = loc.get('left', 0), loc.get('top', 0), loc.get('width', 0), loc.get('height', 0)
                # 转换为平坦四边形边界框（类似于EasyOCR）
                bbox_flat = [left, top, left + width, top, left + width, top + height, left, top + height]
                ocr_results.append(OCRResult(text, confidence, bbox_flat).to_dict())
            
            return ocr_results
        
        except Exception as e:
            logger.error(f"BaiduOCR识别失败: {str(e)}")
            raise
    
    def get_engine_info(self) -> Dict[str, Any]:
        return {
            "name": "BaiduOCR",
            "version": "1.0.0",
            "languages": ["CHN_ENG", "ENG"],  # 支持的中英、英文等
            "initialized": self.initialized
        }