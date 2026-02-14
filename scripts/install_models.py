"""
模型下载脚本
用于预先下载所需的AI模型文件，支持离线部署
"""
import os
import sys
from pathlib import Path


def download_whisper_model(model_size: str = "small", save_dir: str = None):
    """
    下载Whisper模型
    
    Args:
        model_size: 模型大小
        save_dir: 保存目录
    """
    print(f"正在下载Whisper {model_size}模型...")
    
    try:
        import whisper
        
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
            model_path = Path(save_dir) / f"{model_size}.pt"
            
            if model_path.exists():
                print(f"模型已存在: {model_path}")
                return str(model_path)
        
        model = whisper.load_model(model_size)
        
        if save_dir:
            import torch
            save_path = Path(save_dir) / f"{model_size}.pt"
            torch.save(model.state_dict(), save_path)
            print(f"模型已保存到: {save_path}")
        
        print("Whisper模型下载完成")
        return True
        
    except ImportError:
        print("错误: 请先安装openai-whisper: pip install openai-whisper")
        return False
    except Exception as e:
        print(f"下载Whisper模型失败: {e}")
        return False


def download_paddleocr_models(save_dir: str = None):
    """
    下载PaddleOCR模型
    
    Args:
        save_dir: 保存目录
    """
    print("正在下载PaddleOCR模型...")
    
    try:
        from paddleocr import PaddleOCR
        
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
            
            det_dir = os.path.join(save_dir, "det")
            rec_dir = os.path.join(save_dir, "rec")
            cls_dir = os.path.join(save_dir, "cls")
            
            os.makedirs(det_dir, exist_ok=True)
            os.makedirs(rec_dir, exist_ok=True)
            os.makedirs(cls_dir, exist_ok=True)
        
        init_kwargs = {
            "use_textline_orientation": True,
            "lang": "ch"
        }
        
        if save_dir:
            init_kwargs["text_detection_model_dir"] = det_dir
            init_kwargs["text_recognition_model_dir"] = rec_dir
            init_kwargs["textline_orientation_model_dir"] = cls_dir
        
        ocr = PaddleOCR(**init_kwargs)
        
        print("PaddleOCR模型下载完成")
        return True
        
    except ImportError:
        print("错误: 请先安装paddleocr: pip install paddlepaddle paddleocr")
        return False
    except Exception as e:
        print(f"下载PaddleOCR模型失败: {e}")
        return False


def main():
    """主函数"""
    base_dir = Path(__file__).parent.parent
    
    whisper_dir = base_dir / "models" / "whisper"
    paddleocr_dir = base_dir / "models" / "paddleocr"
    
    print("=" * 50)
    print("离线办公助手 - 模型下载工具")
    print("=" * 50)
    
    print("\n[1/2] 下载Whisper模型...")
    download_whisper_model("small", str(whisper_dir))
    
    print("\n[2/2] 下载PaddleOCR模型...")
    download_paddleocr_models(str(paddleocr_dir))
    
    print("\n" + "=" * 50)
    print("所有模型下载完成！")
    print("=" * 50)


if __name__ == "__main__":
    main()
