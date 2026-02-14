@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo   OfficeTools - Starting
echo ========================================
echo.

cd /d %~dp0

set PYTHON_DIR=%~dp0python
set PYTHON_EXE=%PYTHON_DIR%\python.exe
set PYTHON_VERSION=3.10.11

if exist "%PYTHON_EXE%" goto :python_ready

echo [1/5] Downloading Python %PYTHON_VERSION% (embeddable)...
curl -L -o python.zip "https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-embed-amd64.zip"
if errorlevel 1 (
    echo Error: Cannot download Python.
    pause
    exit /b 1
)

echo [2/5] Extracting Python...
if not exist "%PYTHON_DIR%" mkdir "%PYTHON_DIR%"
tar -xf python.zip -C "%PYTHON_DIR%"
del python.zip

echo [3/5] Configuring Python for pip support...
cd /d "%PYTHON_DIR%"
for %%f in (python*._pth) do (
    echo Lib/site-packages>> "%%f"
    powershell -Command "(Get-Content '%%f') -replace '#import site', 'import site' | Set-Content '%%f'"
)
cd /d %~dp0

echo [4/5] Installing pip...
curl -L -o "%PYTHON_DIR%\get-pip.py" "https://bootstrap.pypa.io/get-pip.py"
"%PYTHON_EXE%" "%PYTHON_DIR%\get-pip.py" --no-warn-script-location

echo [5/5] Creating directories...
if not exist "%PYTHON_DIR%\Lib\site-packages" mkdir "%PYTHON_DIR%\Lib\site-packages"

:python_ready
echo [1/5] Python ready.
echo.
echo [2/5] Installing dependencies...
"%PYTHON_EXE%" -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --no-warn-script-location

echo [3/5] Installing PaddlePaddle...
"%PYTHON_EXE%" -m pip install paddlepaddle==2.6.1 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/ --no-warn-script-location

echo [4/5] Checking VC++ Redistributable...
reg query "HKLM\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" /v Installed 2>nul | find "0x1" >nul
if errorlevel 1 (
    echo Downloading VC++ Redistributable...
    curl -L -o vc_redist.exe "https://aka.ms/vs/17/release/vc_redist.x64.exe"
    vc_redist.exe /install /quiet /norestart
    del vc_redist.exe 2>nul
)

echo.
echo ========================================
echo   Service starting...
echo ========================================
echo.

echo [5/5] Starting server...
set PYTHONPATH=%~dp0
"%PYTHON_EXE%" "%~dp0backend\run.py"

pause
