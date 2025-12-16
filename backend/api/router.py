# backend/api/router.py
from fastapi import APIRouter
# 导入你定义的各种路由端点，例如我们之前讨论的 receipts_ocr
from api.endpoints import receipt_ocr  
import logging
logger = logging.getLogger(__name__)

# 确保这个变量名是 api_router
api_router = APIRouter()  # 这行是关键！

# 将各个模块的路由器包含到总路由器中，并可以设置前缀
api_router.include_router(receipt_ocr.router, prefix="", tags=["OCR"])
# 打印包含后的路由（可选调试）
for route in api_router.routes:
    logger.debug(f"api_router 路由: {route.path} - 方法: {route.methods}")