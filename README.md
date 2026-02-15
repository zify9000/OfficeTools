# OfficeTools - 离线办公助手

windows一键包，离线环境下的办公工具集成，支持语音转文字、PDF转Word、图片OCR等功能。

## 项目特点

- **完全离线运行** - 无需联网即可使用所有功能
- **一键启动** - 自动下载 Python 并创建独立环境
- **Web界面** - 基于 FastAPI 的现代化 Web 界面
- **RESTful API** - 提供标准 API 接口，方便集成

## 功能模块

| 模块 | 功能 | 技术方案 |
|-----|------|---------|
| ASR | 语音转文字 | OpenAI Whisper |
| PDF | PDF转Word | pdf2docx |
| OCR | 图片文字识别 | PaddleOCR |

## 快速开始

### 一键启动

双击运行 `start.bat`，脚本会自动完成以下操作：

1. 下载 Python 3.10.11 嵌入式版本到项目 `python` 目录
2. 配置 pip 支持
3. 安装所有依赖
4. 安装 PaddlePaddle 2.6.1
5. 检查并安装 VC++ 运行库
6. 启动服务

### 访问服务

打开浏览器访问: http://127.0.0.1:50000

## 项目结构

```
OfficeTools/
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── main.py         # 应用入口
│   │   ├── config.py       # 配置管理
│   │   ├── routers/        # API 路由
│   │   ├── services/       # 业务服务
│   │   └── models/         # 数据模型
│   └── run.py
├── frontend/               # 前端代码
│   ├── static/            # 静态资源
│   └── templates/         # HTML 模板
├── models/                 # 模型文件目录
│   ├── whisper/           # Whisper 模型
│   └── paddleocr/         # PaddleOCR 模型
├── python/                 # 独立 Python 环境（自动创建）
├── tools/                  # 工具程序
│   └── ffmpeg.exe         # FFmpeg 可执行文件
├── test/                   # 测试文件
├── config.yaml            # 配置文件
├── requirements.txt       # 依赖列表
└── start.bat              # 启动脚本
```

## 配置说明

编辑 `config.yaml` 文件进行配置：

```yaml
server:
  host: "127.0.0.1"
  port: 50000
  debug: false

asr:
  model_size: "small"      # Whisper 模型大小: tiny, base, small, medium, large
  language: "zh"           # 默认语言

ocr:
  lang: "ch"               # OCR 语言: ch, en

pdf:
  dpi: 300                 # PDF 渲染 DPI
```

## API 接口

### 语音转文字

```bash
# 上传音频文件
POST /api/asr/transcribe

# 异步处理
POST /api/asr/transcribe/async
GET /api/asr/task/{task_id}
```

### PDF转Word

```bash
# 上传PDF文件
POST /api/pdf/convert

# 异步处理
POST /api/pdf/convert/async
GET /api/pdf/task/{task_id}
```

### 图片OCR

```bash
# 上传图片
POST /api/ocr/recognize

# 批量识别
POST /api/ocr/recognize/batch

# 异步处理
POST /api/ocr/recognize/async
GET /api/ocr/task/{task_id}
```

## 开发历程

### 🤖 AI 驱动开发

本项目使用 **GLM-5 + Trae** 完成，历时约 **4 小时**，**无人工手动编写代码**。

AI 产品经理的黄金时期 —— 想法即代码。

### 🚧 踩坑记录

#### 1. PaddlePaddle 3.x 与 oneDNN 兼容性问题

**问题描述**: PaddlePaddle 3.x 版本在 Windows 上与 oneDNN 存在兼容性问题，导致 OCR 服务无法正常初始化。

**解决方案**: 降级到 PaddlePaddle 2.6.1 版本

```bash
pip install paddlepaddle==2.6.1 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
```

#### 2. Whisper 依赖 FFmpeg 问题

**问题描述**: OpenAI Whisper 依赖 FFmpeg 进行音频处理，但 FFmpeg 无法通过 pip 安装。

**解决方案**: 
1. 安装 `imageio-ffmpeg` 包
2. 将 `imageio-ffmpeg` 的可执行文件复制到项目的 `tools` 目录，重命名为 `ffmpeg.exe`

```bash
pip install imageio-ffmpeg
# 可执行文件位置: python/Lib/site-packages/imageio_ffmpeg/binaries/
```

## 环境要求

- Windows 10/11
- 无需预装 Python（start.bat 会自动下载）

## 许可证

MIT License
