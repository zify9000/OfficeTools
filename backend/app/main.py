"""
离线办公助手 - 主应用入口
提供语音转文字、PDF转Word、图片OCR等功能
"""
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.config import config
from backend.app.routers import asr, pdf2word, ocr


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    print("正在启动离线办公助手...")
    print(f"服务地址: http://{config.server['host']}:{config.server['port']}")
    yield
    print("正在关闭离线办公助手...")


app = FastAPI(
    title="离线办公助手",
    description="离线环境下的办公工具集成，支持语音转文字、PDF转Word、图片OCR等功能",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

base_path = Path(__file__).parent.parent.parent
static_path = base_path / "frontend" / "static"
templates_path = base_path / "frontend" / "templates"

app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
templates = Jinja2Templates(directory=str(templates_path))

app.include_router(asr.router, prefix="/api/asr", tags=["语音转文字"])
app.include_router(pdf2word.router, prefix="/api/pdf", tags=["PDF转Word"])
app.include_router(ocr.router, prefix="/api/ocr", tags=["图片OCR"])


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """主页"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "message": "服务运行正常"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host=config.server["host"],
        port=config.server["port"],
        reload=config.server.get("debug", False)
    )
