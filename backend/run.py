"""
离线办公助手启动脚本
"""
import uvicorn
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(project_root))

from backend.app.config import config


if __name__ == "__main__":
    uvicorn.run(
        "backend.app.main:app",
        host=config.server["host"],
        port=config.server["port"],
        reload=config.server.get("debug", False)
    )
