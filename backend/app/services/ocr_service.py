"""
OCR识别服务模块
使用PaddleOCR实现图片文字识别功能
"""
import os
import time
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional

from backend.app.config import config


class OcrService:
    """OCR识别服务类"""
    
    _instance = None
    _ocr = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._ocr is None:
            self._load_model()
    
    def _load_model(self) -> None:
        """加载PaddleOCR模型"""
        try:
            from paddleocr import PaddleOCR
            
            lang = config.ocr.get("lang", "ch")
            
            print("加载PaddleOCR模型...")
            self._ocr = PaddleOCR(lang=lang)
            print("PaddleOCR模型加载完成")
            
        except ImportError:
            print("警告: PaddleOCR未安装，OCR功能不可用")
            print("请安装: pip install paddleocr")
            self._ocr = None
        except Exception as e:
            print(f"加载PaddleOCR模型失败: {e}")
            self._ocr = None
    
    def is_available(self) -> bool:
        """检查服务是否可用"""
        return self._ocr is not None
    
    def recognize(
        self,
        image_path: str,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        识别图片中的文字
        
        Args:
            image_path: 图片文件路径
            language: 语言代码，如'ch'、'en'
        
        Returns:
            包含识别结果的字典
        """
        if not self.is_available():
            raise RuntimeError("OCR服务不可用")
        
        start_time = time.time()
        
        result = self._ocr.ocr(image_path, cls=True)
        
        duration = time.time() - start_time
        
        text_results = []
        all_text = []
        total_confidence = 0
        text_count = 0
        
        if result and result[0]:
            for line in result[0]:
                if line is None:
                    continue
                try:
                    box = line[0]
                    text = line[1][0]
                    confidence = line[1][1]
                    
                    text_results.append({
                        "text": text,
                        "box": box,
                        "confidence": round(float(confidence), 4)
                    })
                    all_text.append(text)
                    total_confidence += float(confidence)
                    text_count += 1
                except (IndexError, TypeError) as e:
                    print(f"解析OCR结果失败: {e}")
                    continue
        
        avg_confidence = total_confidence / text_count if text_count > 0 else 0
        
        return {
            "text": "\n".join(all_text),
            "results": text_results,
            "confidence": round(avg_confidence, 4),
            "duration": duration
        }
    
    def recognize_batch(
        self,
        image_paths: List[str],
        language: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        批量识别多张图片
        
        Args:
            image_paths: 图片文件路径列表
            language: 语言代码
        
        Returns:
            识别结果列表
        """
        results = []
        for path in image_paths:
            try:
                result = self.recognize(path, language)
                result["image_path"] = path
                results.append(result)
            except Exception as e:
                results.append({
                    "image_path": path,
                    "error": str(e)
                })
        return results
    
    async def recognize_async(
        self,
        image_path: str,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        异步识别图片文字
        
        Args:
            image_path: 图片文件路径
            language: 语言代码
        
        Returns:
            识别结果字典
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.recognize(image_path, language)
        )


ocr_service = OcrService()
