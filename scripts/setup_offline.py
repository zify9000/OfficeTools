"""
离线环境部署脚本
用于打包和部署到离线环境
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path


def create_offline_package(output_dir: str = "offline_package"):
    """
    创建离线部署包
    
    Args:
        output_dir: 输出目录
    """
    base_dir = Path(__file__).parent.parent
    output_path = base_dir / output_dir
    
    print(f"正在创建离线部署包: {output_path}")
    
    if output_path.exists():
        shutil.rmtree(output_path)
    
    output_path.mkdir(parents=True)
    
    dirs_to_copy = [
        "backend",
        "frontend",
        "models",
        "scripts"
    ]
    
    files_to_copy = [
        "config.yaml",
        "requirements.txt",
        ".gitignore"
    ]
    
    for dir_name in dirs_to_copy:
        src = base_dir / dir_name
        dst = output_path / dir_name
        if src.exists():
            shutil.copytree(src, dst)
            print(f"  复制目录: {dir_name}")
    
    for file_name in files_to_copy:
        src = base_dir / file_name
        dst = output_path / file_name
        if src.exists():
            shutil.copy2(src, dst)
            print(f"  复制文件: {file_name}")
    
    print("\n创建启动脚本...")
    
    start_bat = output_path / "start.bat"
    start_bat.write_text("""@echo off
echo 正在启动离线办公助手...
cd /d %~dp0

if not exist "venv" (
    echo 正在创建虚拟环境...
    python -m venv venv
)

call venv\\Scripts\\activate.bat

pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

python -m backend.run

pause
""", encoding='utf-8')
    
    start_sh = output_path / "start.sh"
    start_sh.write_text("""#!/bin/bash
echo "正在启动离线办公助手..."
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "正在创建虚拟环境..."
    python3 -m venv venv
fi

source venv/bin/activate

pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

python -m backend.run
""", encoding='utf-8')
    
    readme = output_path / "README.txt"
    readme.write_text("""
离线办公助手 - 部署说明
========================

1. 首次运行
   - Windows: 双击 start.bat
   - Linux: 执行 ./start.sh

2. 访问地址
   - 浏览器打开: http://localhost:8000

3. 功能说明
   - 语音转文字: 支持多种音频格式
   - PDF转Word: 保持原有格式
   - 图片OCR: 支持中英文识别

4. 注意事项
   - 首次运行会自动安装依赖
   - 模型文件较大，请耐心等待
   - 建议使用Python 3.8+

""", encoding='utf-8')
    
    print(f"\n离线部署包创建完成: {output_path}")
    print("请将此目录复制到离线环境使用")


def download_pip_packages(save_dir: str = "pip_packages"):
    """
    下载pip依赖包（用于离线安装）
    
    Args:
        save_dir: 保存目录
    """
    base_dir = Path(__file__).parent.parent
    output_path = base_dir / save_dir
    
    print(f"正在下载pip依赖包到: {output_path}")
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        sys.executable, "-m", "pip", "download",
        "-r", str(base_dir / "requirements.txt"),
        "-d", str(output_path),
        "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"\npip依赖包下载完成: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"下载失败: {e}")


def main():
    """主函数"""
    print("=" * 50)
    print("离线办公助手 - 部署工具")
    print("=" * 50)
    
    print("\n请选择操作:")
    print("1. 创建离线部署包")
    print("2. 下载pip依赖包")
    print("3. 全部执行")
    
    choice = input("\n请输入选项 (1/2/3): ").strip()
    
    if choice == "1":
        create_offline_package()
    elif choice == "2":
        download_pip_packages()
    elif choice == "3":
        create_offline_package()
        download_pip_packages()
    else:
        print("无效选项")


if __name__ == "__main__":
    main()
