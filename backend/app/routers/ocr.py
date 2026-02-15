"""
图片OCR API路由
提供图片上传和文字识别接口
"""
import os
import uuid
import aiofiles
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse

from backend.app.config import config
from backend.app.models.schemas import OcrResponse, OcrResult, BaseResponse, TaskStatus
from backend.app.services.ocr_service import ocr_service


router = APIRouter()

tasks_store: dict = {}

ALLOWED_IMAGE_TYPES = [
    "image/jpeg", "image/jpg", "image/png", "image/bmp",
    "image/tiff", "image/webp", "image/gif"
]

ALLOWED_EXTENSIONS = [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp", ".gif"]


async def save_upload_file(upload_file: UploadFile, save_dir: str) -> str:
    """
    保存上传的文件
    
    Args:
        upload_file: 上传的文件对象
        save_dir: 保存目录
    
    Returns:
        保存后的文件路径
    """
    file_ext = os.path.splitext(upload_file.filename)[1]
    file_name = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(save_dir, file_name)
    
    async with aiofiles.open(file_path, 'wb') as f:
        content = await upload_file.read()
        await f.write(content)
    
    return file_path


async def process_ocr_task(task_id: str, image_path: str, language: Optional[str]):
    """后台处理OCR任务"""
    try:
        tasks_store[task_id]["status"] = "processing"
        tasks_store[task_id]["progress"] = 0.3
        
        result = await ocr_service.recognize_async(image_path, language)
        
        tasks_store[task_id]["progress"] = 0.8
        
        output_dir = os.path.join(config.paths["outputs"], "ocr")
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"{task_id}.txt")
        
        async with aiofiles.open(output_file, 'w', encoding='utf-8') as f:
            await f.write(result["text"])
        
        tasks_store[task_id]["status"] = "completed"
        tasks_store[task_id]["progress"] = 1.0
        tasks_store[task_id]["result"] = {
            "text": result["text"],
            "confidence": result["confidence"],
            "duration": result["duration"],
            "output_file": output_file
        }
        
        if os.path.exists(image_path):
            os.remove(image_path)
            
    except Exception as e:
        tasks_store[task_id]["status"] = "failed"
        tasks_store[task_id]["message"] = str(e)


@router.post("/recognize", response_model=OcrResponse)
async def recognize_image(
    file: UploadFile = File(..., description="图片文件"),
    language: Optional[str] = Form(None, description="语言代码，如ch、en")
):
    """
    识别图片中的文字
    
    支持的图片格式: jpg, jpeg, png, bmp, tiff, webp, gif
    
    - **file**: 图片文件
    - **language**: 语言代码，不指定则自动检测
    """
    if not ocr_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="OCR服务不可用，请检查PaddleOCR是否正确安装"
        )
    
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的图片格式，支持: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    upload_dir = config.paths["uploads"]
    
    try:
        image_path = await save_upload_file(file, upload_dir)
        
        result = await ocr_service.recognize_async(image_path, language)
        
        output_dir = os.path.join(config.paths["outputs"], "ocr")
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"{uuid.uuid4()}.txt")
        
        async with aiofiles.open(output_file, 'w', encoding='utf-8') as f:
            await f.write(result["text"])
        
        if os.path.exists(image_path):
            os.remove(image_path)
        
        ocr_results = [
            OcrResult(
                text=r["text"],
                boxes=r["box"],
                confidence=r["confidence"]
            )
            for r in result["results"]
        ]
        
        return OcrResponse(
            success=True,
            message="识别成功",
            data=ocr_results
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"识别失败: {str(e)}")


@router.post("/recognize/batch", response_model=List[OcrResponse])
async def recognize_images_batch(
    files: List[UploadFile] = File(..., description="图片文件列表"),
    language: Optional[str] = Form(None, description="语言代码")
):
    """
    批量识别多张图片
    
    - **files**: 图片文件列表
    - **language**: 语言代码
    """
    if not ocr_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="OCR服务不可用"
        )
    
    upload_dir = config.paths["uploads"]
    results = []
    
    for file in files:
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            results.append(OcrResponse(
                success=False,
                message=f"不支持的图片格式: {file.filename}"
            ))
            continue
        
        try:
            image_path = await save_upload_file(file, upload_dir)
            result = await ocr_service.recognize_async(image_path, language)
            
            output_dir = os.path.join(config.paths["outputs"], "ocr")
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, f"{uuid.uuid4()}.txt")
            
            result_text = "\n".join([r["text"] for r in result["results"]])
            async with aiofiles.open(output_file, 'w', encoding='utf-8') as f:
                await f.write(result_text)
            
            if os.path.exists(image_path):
                os.remove(image_path)
            
            ocr_results = [
                OcrResult(
                    text=r["text"],
                    boxes=r["box"],
                    confidence=r["confidence"]
                )
                for r in result["results"]
            ]
            
            results.append(OcrResponse(
                success=True,
                message="识别成功",
                data=ocr_results
            ))
            
        except Exception as e:
            results.append(OcrResponse(
                success=False,
                message=f"识别失败: {str(e)}"
            ))
    
    return results


@router.post("/recognize/async", response_model=TaskStatus)
async def recognize_image_async(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="图片文件"),
    language: Optional[str] = Form(None, description="语言代码")
):
    """
    异步识别图片（适合大图片）
    
    返回任务ID，可通过/task/{task_id}查询进度
    """
    if not ocr_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="OCR服务不可用"
        )
    
    upload_dir = config.paths["uploads"]
    image_path = await save_upload_file(file, upload_dir)
    
    task_id = str(uuid.uuid4())
    tasks_store[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "progress": 0.0,
        "message": "任务已创建"
    }
    
    background_tasks.add_task(process_ocr_task, task_id, image_path, language)
    
    return TaskStatus(**tasks_store[task_id])


@router.get("/task/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """获取异步任务状态"""
    if task_id not in tasks_store:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return TaskStatus(**tasks_store[task_id])


@router.get("/download/{task_id}")
async def download_result(task_id: str):
    """下载识别结果文件"""
    if task_id not in tasks_store:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = tasks_store[task_id]
    
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="任务尚未完成")
    
    output_file = task["result"].get("output_file")
    
    if not output_file or not os.path.exists(output_file):
        raise HTTPException(status_code=404, detail="结果文件不存在")
    
    return FileResponse(
        output_file,
        media_type="text/plain",
        filename=f"ocr_result_{task_id}.txt"
    )


@router.get("/status")
async def get_service_status():
    """获取服务状态"""
    return {
        "available": ocr_service.is_available(),
        "language": config.ocr.get("lang", "ch")
    }
