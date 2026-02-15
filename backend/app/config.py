"""
配置管理模块
负责加载和管理应用程序配置
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict


class ConfigManager:
    """配置管理器类"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self._load_config()
    
    def _load_config(self) -> None:
        """加载配置文件"""
        config_path = Path(__file__).parent.parent.parent / "config.yaml"
        
        if not config_path.exists():
            self._config = self._get_default_config()
        else:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
        
        self._resolve_paths()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "server": {
                "host": "0.0.0.0",
                "port": 8000,
                "debug": True
            },
            "paths": {
                "uploads": "uploads",
                "outputs": "outputs",
                "models": "models"
            },
            "asr": {
                "model_size": "small",
                "language": "zh",
                "model_path": "models/whisper"
            },
            "ocr": {
                "use_gpu": False,
                "lang": "ch",
                "model_path": "models/paddleocr"
            },
            "pdf": {
                "dpi": 300
            }
        }
    
    def _resolve_paths(self) -> None:
        """解析并创建路径"""
        base_path = Path(__file__).parent.parent.parent
        
        for key, path in self._config.get("paths", {}).items():
            resolved_path = base_path / path
            self._config["paths"][key] = str(resolved_path)
            resolved_path.mkdir(parents=True, exist_ok=True)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项
        
        Args:
            key: 配置键，支持点分隔符如 'server.host'
            default: 默认值
        
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    @property
    def server(self) -> Dict[str, Any]:
        """获取服务器配置"""
        return self._config.get("server", {})
    
    @property
    def paths(self) -> Dict[str, Any]:
        """获取路径配置"""
        return self._config.get("paths", {})
    
    @property
    def asr(self) -> Dict[str, Any]:
        """获取ASR配置"""
        return self._config.get("asr", {})
    
    @property
    def ocr(self) -> Dict[str, Any]:
        """获取OCR配置"""
        return self._config.get("ocr", {})
    
    @property
    def pdf(self) -> Dict[str, Any]:
        """获取PDF配置"""
        return self._config.get("pdf", {})


config = ConfigManager()
