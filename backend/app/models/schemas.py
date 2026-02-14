"""
响应模型定义
定义API响应的数据结构
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[Dict[str, Any]] = None


class AsrResult(BaseModel):
    """语音识别结果模型"""
    text: str
    language: str
    duration: float


class AsrResponse(BaseResponse):
    """语音识别响应模型"""
    data: Optional[AsrResult] = None


class OcrResult(BaseModel):
    """OCR识别结果模型"""
    text: str
    boxes: List[List[float]]
    confidence: float


class OcrResponse(BaseResponse):
    """OCR响应模型"""
    data: Optional[List[OcrResult]] = None


class PdfConvertResult(BaseModel):
    """PDF转换结果模型"""
    output_path: str
    page_count: int
    word_count: int


class PdfConvertResponse(BaseResponse):
    """PDF转换响应模型"""
    data: Optional[PdfConvertResult] = None


class TaskStatus(BaseModel):
    """任务状态模型"""
    task_id: str
    status: str
    progress: float
    message: str
    result: Optional[Dict[str, Any]] = None
