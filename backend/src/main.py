"""
应用入口模块

启动 FastAPI 应用服务器

运行方式：
    cd backend
    python -m src.main
    或
    uvicorn src.app:app --reload
"""

import sys
from pathlib import Path

# 确保项目根目录在 Python 路径中
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import uvicorn

from src.app import app
from src.core.config import settings
from src.utils.logger import get_logger

log = get_logger("main")


def main() -> None:
    """启动应用"""
    log.info(f"启动服务器: http://{settings.host}:{settings.port}")

    uvicorn.run(
        "src.app:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        reload=settings.debug,
        log_level="info",
        access_log=False,  # 使用自定义日志中间件
    )


if __name__ == "__main__":
    main()