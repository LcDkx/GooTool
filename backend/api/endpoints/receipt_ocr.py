from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import io
from PIL import Image
import logging

from services.ocr import ocr_manager
from services.receipt_parser import ReceiptParser

router = APIRouter()
logger = logging.getLogger(__name__)
receipt_parser = ReceiptParser()

@router.post("/ocr/receipt")
async def process_receipt(
    file: UploadFile = File(..., description="上传的购物小票图片"),
    engine: str = Query("baiduocr", description="OCR引擎选择"),
    columns: Optional[List[str]] = Query(None, description="需要返回的列名")
):
    """处理购物小票识别请求"""
    logger.info(f"收到请求: 方法=POST, 路径=/ocr/receipt, engine={engine}, columns={columns}")
    try:
        # 验证文件类型
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="请上传图片文件")
        
        # 读取图片数据
        image_data = await file.read()
        
        # 使用指定OCR引擎识别文字
        ocr_results = ocr_manager.recognize_text(image_data, engine_name=engine)
        
        # 解析小票内容
        parsed_data = receipt_parser.parse_receipt_text(ocr_results)
        
        # 根据用户选择的列过滤数据
        filtered_data = _filter_columns(parsed_data, columns)
        
        return JSONResponse({
            "success": True,
            "engine_used": engine,
            "data": parsed_data.get("items", []),  # 始终返回 items 数组
            "available_columns": list(parsed_data.keys()),
            "confidence": parsed_data.get("confidence", 0),
            "full_data": filtered_data  # 可选：额外字段返回完整对象
        })
        
    except Exception as e:
        logger.error(f"处理小票识别失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")

@router.get("/ocr/engines")
async def get_available_engines():
    """获取可用的OCR引擎列表"""
    engines = ocr_manager.get_available_engines()
    engines_info = {}
    
    for engine_name in engines:
        engines_info[engine_name] = ocr_manager.get_engine_info(engine_name)
    
    return {
        "available_engines": engines,
        "engines_info": engines_info,
        "default_engine": ocr_manager.default_engine
    }

def _filter_columns(data: Dict[str, Any], columns: Optional[List[str]]) -> Dict[str, Any]:
    """根据用户选择的列过滤数据"""
    if not columns:
        return data
    
    filtered = {}
    for col in columns:
        if col in data:
            filtered[col] = data[col]
        else:
            # 如果列不存在，尝试在嵌套结构中查找
            for key, value in data.items():
                if isinstance(value, dict) and col in value:
                    filtered[col] = value[col]
    
    return filtered