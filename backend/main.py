from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

from services.ocr import ocr_manager
from api.router import api_router

from fastapi.staticfiles import StaticFiles


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 新的 lifespan 事件处理器
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    生命周期事件处理器
    - yield 之前的代码在应用启动时执行
    - yield 之后的代码在应用关闭时执行
    """
    # 启动逻辑 (替代原来的 @app.on_event("startup"))
    logger.info("正在初始化OCR引擎...")
    try:
        if not ocr_manager.initialize_engines():
            logger.error("OCR引擎初始化失败，服务可能无法正常工作")
        else:
            logger.info("OCR引擎初始化完成")
    except Exception as e:
        logger.error(f"OCR引擎初始化过程中发生错误: {str(e)}")
    
    # yield 标志应用已启动完成，可以开始处理请求
    yield
    
    # 关闭逻辑 (替代原来的 @app.on_event("shutdown"))
    logger.info("正在执行清理操作...")
    # 可以在此添加资源释放等清理代码

# 创建FastAPI应用并传入lifespan参数
app = FastAPI(title="购物小票OCR识别系统", version="1.0.0", lifespan=lifespan)
app.include_router(api_router, prefix="/api/v1")
# print("注册路由完成")
# for route in app.routes:
#     print(f"注册路由: {route.path} - 方法: {route.methods}")
# print("路由打印完成")
# 假设你的前端文件放在项目根目录的 frontend 文件夹中
app.mount("/", StaticFiles(directory="/home/admin/goodtool/frontend", html=True), name="static")
# 配置CORS（保持不变）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
async def root():
    return {"message": "购物小票OCR识别系统已就绪"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)