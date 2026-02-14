/**
 * 离线办公助手前端应用
 * 处理文件上传、API调用和结果展示
 */

const API_BASE = '';

let currentFiles = {
    asr: null,
    pdf: null,
    ocr: []
};

let downloadUrls = {
    asr: null,
    pdf: null,
    ocr: null
};


/**
 * 显示提示消息
 * @param {string} message - 消息内容
 * @param {string} type - 消息类型 (success/error)
 */
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}


/**
 * 格式化文件大小
 * @param {number} bytes - 字节数
 * @returns {string} 格式化后的文件大小
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}


/**
 * 初始化标签页切换
 */
function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const sections = document.querySelectorAll('.tool-section');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.dataset.tab;
            
            tabBtns.forEach(b => b.classList.remove('active'));
            sections.forEach(s => s.classList.remove('active'));
            
            btn.classList.add('active');
            document.getElementById(`${tabId}-section`).classList.add('active');
        });
    });
}


/**
 * 初始化文件上传区域
 * @param {string} type - 模块类型 (asr/pdf/ocr)
 */
function initUploadArea(type) {
    const uploadArea = document.getElementById(`${type}-upload`);
    const fileInput = document.getElementById(`${type}-file`);
    
    uploadArea.addEventListener('click', () => fileInput.click());
    
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        handleFiles(type, e.dataTransfer.files);
    });
    
    fileInput.addEventListener('change', (e) => {
        handleFiles(type, e.target.files);
    });
}


/**
 * 处理选择的文件
 * @param {string} type - 模块类型
 * @param {FileList} files - 文件列表
 */
function handleFiles(type, files) {
    const fileInfo = document.getElementById(`${type}-file-info`);
    const convertBtn = document.getElementById(`${type}-convert`);
    
    if (type === 'ocr') {
        currentFiles.ocr = Array.from(files);
        if (currentFiles.ocr.length > 0) {
            const names = currentFiles.ocr.map(f => f.name).join(', ');
            fileInfo.innerHTML = `<span class="file-name">${currentFiles.ocr.length} 个文件</span><span class="file-size">${names.substring(0, 50)}${names.length > 50 ? '...' : ''}</span>`;
            fileInfo.classList.add('show');
            convertBtn.disabled = false;
        }
    } else {
        const file = files[0];
        if (file) {
            currentFiles[type] = file;
            fileInfo.innerHTML = `<span class="file-name">${file.name}</span><span class="file-size">${formatFileSize(file.size)}</span>`;
            fileInfo.classList.add('show');
            convertBtn.disabled = false;
        }
    }
}


/**
 * 上传文件到服务器
 * @param {string} url - API地址
 * @param {FormData} formData - 表单数据
 * @returns {Promise} 响应结果
 */
async function uploadFile(url, formData) {
    const response = await fetch(url, {
        method: 'POST',
        body: formData
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '请求失败');
    }
    
    return response.json();
}


/**
 * 显示进度条
 * @param {string} type - 模块类型
 * @param {number} progress - 进度值 (0-1)
 * @param {string} text - 进度文本
 */
function showProgress(type, progress, text) {
    const container = document.getElementById(`${type}-progress`);
    const fill = container.querySelector('.progress-fill');
    const textEl = container.querySelector('.progress-text');
    
    container.hidden = false;
    fill.style.width = `${progress * 100}%`;
    textEl.textContent = text;
}


/**
 * 隐藏进度条
 * @param {string} type - 模块类型
 */
function hideProgress(type) {
    document.getElementById(`${type}-progress`).hidden = true;
}


/**
 * 显示结果区域
 * @param {string} type - 模块类型
 * @param {string} content - 结果内容
 * @param {object} info - 附加信息
 */
function showResult(type, content, info = {}) {
    const resultArea = document.getElementById(`${type}-result`);
    const resultText = resultArea.querySelector('.result-text') || resultArea.querySelector('.result-info');
    
    if (resultText.classList.contains('result-text')) {
        resultText.textContent = content;
    } else {
        resultText.innerHTML = content;
    }
    
    resultArea.hidden = false;
}


/**
 * 隐藏结果区域
 * @param {string} type - 模块类型
 */
function hideResult(type) {
    document.getElementById(`${type}-result`).hidden = true;
}


/**
 * 处理语音转文字
 */
async function handleAsrConvert() {
    const file = currentFiles.asr;
    if (!file) return;
    
    const language = document.getElementById('asr-language').value;
    const convertBtn = document.getElementById('asr-convert');
    
    convertBtn.disabled = true;
    hideResult('asr');
    showProgress('asr', 0.3, '正在上传文件...');
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        if (language) formData.append('language', language);
        
        showProgress('asr', 0.5, '正在识别语音...');
        
        const result = await uploadFile(`${API_BASE}/api/asr/transcribe`, formData);
        
        showProgress('asr', 1, '识别完成');
        
        setTimeout(() => {
            hideProgress('asr');
            showResult('asr', result.data.text);
            showToast('语音识别完成');
        }, 500);
        
    } catch (error) {
        hideProgress('asr');
        showToast(error.message, 'error');
    } finally {
        convertBtn.disabled = false;
    }
}


/**
 * 处理PDF转Word
 */
async function handlePdfConvert() {
    const file = currentFiles.pdf;
    if (!file) return;
    
    const startPage = document.getElementById('pdf-start').value;
    const endPage = document.getElementById('pdf-end').value;
    const dpi = document.getElementById('pdf-dpi').value;
    const convertBtn = document.getElementById('pdf-convert');
    
    convertBtn.disabled = true;
    hideResult('pdf');
    showProgress('pdf', 0.3, '正在上传文件...');
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        if (startPage) formData.append('start_page', startPage);
        if (endPage) formData.append('end_page', endPage);
        formData.append('dpi', dpi);
        
        showProgress('pdf', 0.5, '正在转换PDF...');
        
        const result = await uploadFile(`${API_BASE}/api/pdf/convert`, formData);
        
        showProgress('pdf', 1, '转换完成');
        
        downloadUrls.pdf = result.data.output_path;
        
        setTimeout(() => {
            hideProgress('pdf');
            const infoHtml = `
                <p><strong>页数:</strong> ${result.data.page_count} 页</p>
                <p><strong>字数:</strong> ${result.data.word_count} 字</p>
            `;
            showResult('pdf', infoHtml);
            showToast('PDF转换完成');
        }, 500);
        
    } catch (error) {
        hideProgress('pdf');
        showToast(error.message, 'error');
    } finally {
        convertBtn.disabled = false;
    }
}


/**
 * 处理图片OCR
 */
async function handleOcrConvert() {
    const files = currentFiles.ocr;
    if (files.length === 0) return;
    
    const language = document.getElementById('ocr-language').value;
    const convertBtn = document.getElementById('ocr-convert');
    
    convertBtn.disabled = true;
    hideResult('ocr');
    showProgress('ocr', 0.3, '正在上传文件...');
    
    try {
        const formData = new FormData();
        files.forEach(file => formData.append('files', file));
        if (language) formData.append('language', language);
        
        showProgress('ocr', 0.5, '正在识别文字...');
        
        const results = await uploadFile(`${API_BASE}/api/ocr/recognize/batch`, formData);
        
        showProgress('ocr', 1, '识别完成');
        
        let allText = '';
        results.forEach((result, index) => {
            if (result.success && result.data) {
                const texts = result.data.map(item => item.text).join('\n');
                allText += `=== 图片 ${index + 1} ===\n${texts}\n\n`;
            }
        });
        
        setTimeout(() => {
            hideProgress('ocr');
            showResult('ocr', allText.trim());
            showToast('OCR识别完成');
        }, 500);
        
    } catch (error) {
        hideProgress('ocr');
        showToast(error.message, 'error');
    } finally {
        convertBtn.disabled = false;
    }
}


/**
 * 复制文本到剪贴板
 * @param {string} type - 模块类型
 */
function copyText(type) {
    const resultArea = document.getElementById(`${type}-result`);
    const text = resultArea.querySelector('.result-text').textContent;
    
    navigator.clipboard.writeText(text).then(() => {
        showToast('已复制到剪贴板');
    }).catch(() => {
        showToast('复制失败', 'error');
    });
}


/**
 * 下载结果文件
 * @param {string} type - 模块类型
 */
function downloadFile(type) {
    if (type === 'pdf' && downloadUrls.pdf) {
        window.location.href = `${API_BASE}/api/pdf/download/${downloadUrls.pdf}`;
    } else {
        const resultArea = document.getElementById(`${type}-result`);
        const text = resultArea.querySelector('.result-text').textContent;
        
        const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `result_${Date.now()}.txt`;
        a.click();
        URL.revokeObjectURL(url);
    }
}


/**
 * 初始化应用
 */
function init() {
    initTabs();
    
    initUploadArea('asr');
    initUploadArea('pdf');
    initUploadArea('ocr');
    
    document.getElementById('asr-convert').addEventListener('click', handleAsrConvert);
    document.getElementById('pdf-convert').addEventListener('click', handlePdfConvert);
    document.getElementById('ocr-convert').addEventListener('click', handleOcrConvert);
    
    document.querySelectorAll('.copy-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const section = btn.closest('.tool-section');
            const type = section.id.replace('-section', '');
            copyText(type);
        });
    });
    
    document.querySelectorAll('.download-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const section = btn.closest('.tool-section');
            const type = section.id.replace('-section', '');
            downloadFile(type);
        });
    });
}


document.addEventListener('DOMContentLoaded', init);
