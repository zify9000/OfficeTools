"""
语音识别服务模块
使用Whisper模型实现语音转文字功能
"""
import os
import time
import uuid
import asyncio
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

from backend.app.config import config


class AsrService:
    """语音识别服务类"""
    
    _instance = None
    _model = None
    _ffmpeg_available = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._model is None:
            self._load_model()
    
    def _check_ffmpeg(self) -> bool:
        """
        检查ffmpeg是否可用
        优先检查系统ffmpeg，其次检查imageio-ffmpeg
        
        Returns:
            ffmpeg是否可用
        """
        if self._ffmpeg_available is not None:
            return self._ffmpeg_available
        
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                timeout=5
            )
            self._ffmpeg_available = result.returncode == 0
            if self._ffmpeg_available:
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        try:
            import imageio_ffmpeg
            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            result = subprocess.run(
                [ffmpeg_path, '-version'],
                capture_output=True,
                timeout=5
            )
            self._ffmpeg_available = result.returncode == 0
            if self._ffmpeg_available:
                project_root = Path(__file__).parent.parent.parent.parent
                tools_dir = project_root / "tools"
                tools_dir.mkdir(exist_ok=True)
                ffmpeg_exe = tools_dir / "ffmpeg.exe"
                if not ffmpeg_exe.exists():
                    shutil.copy(ffmpeg_path, ffmpeg_exe)
                ffmpeg_dir_str = str(tools_dir)
                current_path = os.environ.get('PATH', '')
                if ffmpeg_dir_str not in current_path:
                    os.environ['PATH'] = ffmpeg_dir_str + os.pathsep + current_path
                os.environ['FFMPEG_BINARY'] = str(ffmpeg_exe)
                return True
        except (ImportError, Exception):
            pass
        
        self._ffmpeg_available = False
        return self._ffmpeg_available
    
    def _load_model(self) -> None:
        """加载Whisper模型"""
        try:
            import whisper
            
            if not self._check_ffmpeg():
                print("警告: ffmpeg未安装，语音识别功能将无法正常工作")
                print("请安装ffmpeg: conda install ffmpeg -c conda-forge")
                print("或者: pip install imageio-ffmpeg")
            
            model_size = config.asr.get("model_size", "small")
            model_path = config.asr.get("model_path")
            
            model_file = Path(model_path) / f"{model_size}.pt"
            
            if model_file.exists():
                print(f"从本地加载Whisper模型: {model_file}")
                try:
                    self._model = whisper.load_model(str(model_file))
                    print("Whisper模型加载完成")
                    return
                except Exception as e:
                    print(f"本地模型加载失败: {e}，尝试从网络下载...")
            
            print(f"加载Whisper模型: {model_size}")
            self._model = whisper.load_model(model_size)
            print("Whisper模型加载完成")
            
        except ImportError:
            print("警告: Whisper未安装，语音识别功能不可用")
            self._model = None
        except Exception as e:
            print(f"加载Whisper模型失败: {e}")
            self._model = None
    
    def is_available(self) -> bool:
        """检查服务是否可用"""
        return self._model is not None and self._check_ffmpeg()
    
    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        task: str = "transcribe"
    ) -> Dict[str, Any]:
        """
        转录音频文件
        
        Args:
            audio_path: 音频文件路径
            language: 语言代码，如'zh'、'en'
            task: 任务类型，'transcribe'为转录，'translate'为翻译为英文
        
        Returns:
            包含转录结果的字典
        """
        if not self.is_available():
            raise RuntimeError("语音识别服务不可用")
        
        if language is None:
            language = config.asr.get("language", "zh")
        
        start_time = time.time()
        
        result = self._model.transcribe(
            audio_path,
            language=language,
            task=task,
            verbose=False
        )
        
        duration = time.time() - start_time
        
        segments = []
        for segment in result.get("segments", []):
            segments.append({
                "start": segment["start"],
                "end": segment["end"],
                "text": segment["text"].strip()
            })
        
        return {
            "text": result["text"].strip(),
            "language": result.get("language", language),
            "segments": segments,
            "duration": duration
        }
    
    async def transcribe_async(
        self,
        audio_path: str,
        language: Optional[str] = None,
        task: str = "transcribe"
    ) -> Dict[str, Any]:
        """
        异步转录音频文件
        
        Args:
            audio_path: 音频文件路径
            language: 语言代码
            task: 任务类型
        
        Returns:
            包含转录结果的字典
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.transcribe(audio_path, language, task)
        )


asr_service = AsrService()
