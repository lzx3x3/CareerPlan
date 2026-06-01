@echo off
chcp 65001 >nul
echo ========================================
echo   职业规划师 - 后端服务启动
echo ========================================
echo.

cd /d "%~dp0"

REM ===== 使用 careerPlan conda 环境 =====
set PYTHON_PATH=C:\Users\Lenovo\miniconda3\envs\careerPlan\python.exe

REM ===== 检查环境是否存在 =====
if not exist "%PYTHON_PATH%" (
    echo [错误] careerPlan 环境不存在！
    echo 请先创建环境：conda create -n careerPlan python=3.12
    pause
    exit /b 1
)

REM ===== 加载 .env 文件中的环境变量 =====
if exist .env (
    for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
        set "line=%%a"
        if not "!line:~0,1!"=="#" (
            set "%%a=%%b"
        )
    )
)

REM ===== 启动后端（使用 careerPlan 环境）=====
echo 使用 careerPlan 环境启动...
"%PYTHON_PATH%" app.py
pause
