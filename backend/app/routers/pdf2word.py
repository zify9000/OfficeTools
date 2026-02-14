"""
PDF转Word API路由
提供PDF文件上传和转换接口
"""
import os
import uuid
import aiofiles
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from backend.app.config import config
from backend.app.models.schemas import PdfConvertResponse, PdfConvertResult, BaseResponse, TaskStatus
from backend.app.services.pdf_service import pdf_service


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


async def process_pdf_task(
    task_id: str,
    pdf_path: str,
    output_path: str,
    start_page: Optional[int],
    end_page: Optional[int],
    dpi: int
):
    """后台处理PDF转换任务"""
    try:
        tasks_store[task_id]["status"] = "processing"
        tasks_store[task_id]["progress"] = 0.1
        
        result = await pdf_service.convert_async(
            pdf_path,
            output_path,
            start_page or 0,
            end_page,
            dpi
        )
        
        tasks_store[task_id]["status"] = "completed"
        tasks_store[task_id]["progress"] = 1.0
        tasks_store[task_id]["result"] = {
            "output_path": result["output_path"],
            "page_count": result["page_count"],
            "word_count": result["word_count"]
        }
        
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            
    except Exception as e:
        tasks_store[task_id]["status"] = "failed"
        tasks_store[task_id]["message"] = str(e)


@router.post("/convert", response_model=PdfConvertResponse)
async def convert_pdf(
    file: UploadFile = File(..., description="PDF文件"),
    start_page: Optional[int] = Form(None, description="起始页码（从0开始）"),
    end_page: Optional[int] = Form(None, description="结束页码"),
    dpi: int = Form(300, description="渲染DPI")
):
    """
    将PDF转换为Word文档
    
    - **file**: PDF文件
    - **start_page**: 起始页码（从0开始），不指定则从第一页开始
    - **end_page**: 结束页码，不指定则转换到最后一页
    - **dpi**: 渲染DPI，影响图片质量，默认300
    """
    if not pdf_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="PDF转换服务不可用，请安装pdf2docx"
        )
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="请上传PDF文件")
    
    upload_dir = config.paths["uploads"]
    output_dir = config.paths["outputs"]
    
    try:
        pdf_path = await save_upload_file(file, upload_dir)
        
        output_name = f"{uuid.uuid4()}.docx"
        output_path = os.path.join(output_dir, output_name)
        
        result = await pdf_service.convert_async(
            pdf_path,
            output_path,
            start_page or 0,
            end_page,
            dpi
        )
        
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        
        return PdfConvertResponse(
            success=True,
            message="转换成功",
            data=PdfConvertResult(
                output_path=output_name,
                page_count=result["page_count"],
                word_count=result["word_count"]
            )
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"转换失败: {str(e)}")


@router.post("/convert/async", response_model=TaskStatus)
async def convert_pdf_async(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="PDF文件"),
    start_page: Optional[int] = Form(None, description="起始页码"),
    end_page: Optional[int] = Form(None, description="结束页码"),
    dpi: int = Form(300, description="渲染DPI")
):
    """
    异步转换PDF（适合大文件）
    
    返回任务ID，可通过/task/{task_id}查询进度
    """
    if not pdf_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="PDF转换服务不可用"
        )
    
    upload_dir = config.paths["uploads"]
    output_dir = config.paths["outputs"]
    
    pdf_path = await save_upload_file(file, upload_dir)
    
    task_id = str(uuid.uuid4())
    output_path = os.path.join(output_dir, f"{task_id}.docx")
    
    tasks_store[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "progress": 0.0,
        "message": "任务已创建"
    }
    
    background_tasks.add_task(
        process_pdf_task,
        task_id,
        pdf_path,
        output_path,
        start_page,
        end_page,
        dpi
    )
    
    return TaskStatus(**tasks_store[task_id])


@router.get("/task/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """获取异步任务状态"""
    if task_id not in tasks_store:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return TaskStatus(**tasks_store[task_id])


@router.get("/download/{filename}")
async def download_result(filename: str):
    """下载转换结果文件"""
    output_dir = config.paths["outputs"]
    file_path = os.path.join(output_dir, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        file_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename
    )


@router.get("/page-count")
async def get_page_count(file_path: str):
    """
    获取PDF页数
    
    - **file_path**: PDF文件路径
    """
    if not pdf_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="PDF转换服务不可用"
        )
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    try:
        page_count = pdf_service.get_page_count(file_path)
        return {"page_count": page_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取页数失败: {str(e)}")


@router.get("/status")
async def get_service_status():
    """获取服务状态"""
    return {
        "available": pdf_service.is_available()
    }
