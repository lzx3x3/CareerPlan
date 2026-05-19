@echo off
chcp 65001 >nul
echo ========================================
echo   职业规划师 - 一键启动
echo ========================================
echo.

cd /d "%~dp0"

REM ===== Step 1: 清理旧的 Python 进程 =====
echo [1/4] 清理旧进程...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

REM ===== Step 2: 检查 5000 端口 =====
echo [2/4] 检查端口占用...
netstat -ano | findstr ":5000" >nul
if %errorlevel%==0 (
    echo [警告] 5000 端口仍被占用，尝试强制清理...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000" ^| findstr "LISTENING"') do (
        echo 正在终止进程 PID: %%a
        taskkill /F /PID %%a 2>nul
    )
    timeout /t 1 /nobreak >nul
)

REM ===== Step 3: 安装依赖 =====
echo [3/4] 检查依赖...
python -c "import flask" 2>nul
if %errorlevel% neq 0 (
    echo 正在安装依赖...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [错误] 依赖安装失败！
        pause
        exit /b 1
    )
)

REM ===== Step 4: 启动后端 =====
echo [4/4] 启动后端服务...
echo.
echo ========================================
echo   后端启动中，请稍候...
echo ========================================
echo.

REM 加载 .env 文件
if exist .env (
    for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
        set "line=%%a"
        if not "!line:~0,1!"=="#" (
            set "%%a=%%b"
        )
    )
)

REM 启动后端
python app.py
