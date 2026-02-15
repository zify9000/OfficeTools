"""
语音转文字API路由
提供音频文件上传和转录接口
"""
import os
import uuid
import aiofiles
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse

from backend.app.config import config
from backend.app.models.schemas import AsrResponse, AsrResult, BaseResponse, TaskStatus
from backend.app.services.asr_service import asr_service


router = APIRouter()

tasks_store: dict = {}


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


async def process_asr_task(task_id: str, audio_path: str, language: Optional[str]):
    """后台处理语音识别任务"""
    try:
        tasks_store[task_id]["status"] = "processing"
        tasks_store[task_id]["progress"] = 0.3
        
        result = await asr_service.transcribe_async(audio_path, language)
        
        tasks_store[task_id]["progress"] = 0.8
        
        output_dir = os.path.join(config.paths["outputs"], "asr")
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"{task_id}.txt")
        
        async with aiofiles.open(output_file, 'w', encoding='utf-8') as f:
            await f.write(result["text"])
        
        tasks_store[task_id]["status"] = "completed"
        tasks_store[task_id]["progress"] = 1.0
        tasks_store[task_id]["result"] = {
            "text": result["text"],
            "language": result["language"],
            "duration": result["duration"],
            "output_file": output_file
        }
        
        if os.path.exists(audio_path):
            os.remove(audio_path)
            
    except Exception as e:
        tasks_store[task_id]["status"] = "failed"
        tasks_store[task_id]["message"] = str(e)


@router.post("/transcribe", response_model=AsrResponse)
async def transcribe_audio(
    file: UploadFile = File(..., description="音频文件"),
    language: Optional[str] = Form(None, description="语言代码，如zh、en")
):
    """
    转录音频文件
    
    支持的音频格式: mp3, wav, m4a, flac, ogg等
    
    - **file**: 音频文件
    - **language**: 语言代码，不指定则自动检测
    """
    if not asr_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="语音识别服务不可用，请检查Whisper模型是否正确安装"
        )
    
    allowed_types = ["audio/mpeg", "audio/wav", "audio/x-wav", "audio/mp3",
                     "audio/m4a", "audio/x-m4a", "audio/flac", "audio/ogg",
                     "video/mp4"]
    
    upload_dir = config.paths["uploads"]
    
    try:
        audio_path = await save_upload_file(file, upload_dir)
        
        result = await asr_service.transcribe_async(audio_path, language)
        
        output_dir = os.path.join(config.paths["outputs"], "asr")
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"{uuid.uuid4()}.txt")
        
        async with aiofiles.open(output_file, 'w', encoding='utf-8') as f:
            await f.write(result["text"])
        
        if os.path.exists(audio_path):
            os.remove(audio_path)
        
        return AsrResponse(
            success=True,
            message="转录成功",
            data=AsrResult(
                text=result["text"],
                language=result["language"],
                duration=result["duration"]
            )
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"转录失败: {str(e)}")


@router.post("/transcribe/async", response_model=TaskStatus)
async def transcribe_audio_async(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="音频文件"),
    language: Optional[str] = Form(None, description="语言代码")
):
    """
    异步转录音频文件（适合大文件）
    
    返回任务ID，可通过/task/{task_id}查询进度
    """
    if not asr_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="语音识别服务不可用"
        )
    
    upload_dir = config.paths["uploads"]
    audio_path = await save_upload_file(file, upload_dir)
    
    task_id = str(uuid.uuid4())
    tasks_store[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "progress": 0.0,
        "message": "任务已创建"
    }
    
    background_tasks.add_task(process_asr_task, task_id, audio_path, language)
    
    return TaskStatus(**tasks_store[task_id])


@router.get("/task/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """获取异步任务状态"""
    if task_id not in tasks_store:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return TaskStatus(**tasks_store[task_id])


@router.get("/download/{task_id}")
async def download_result(task_id: str):
    """下载转录结果文件"""
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
        filename=f"transcript_{task_id}.txt"
    )


@router.get("/status")
async def get_service_status():
    """获取服务状态"""
    return {
        "available": asr_service.is_available(),
        "model": config.asr.get("model_size", "small")
    }
