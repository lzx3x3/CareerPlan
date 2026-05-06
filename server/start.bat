@echo off
chcp 65001 >nul
echo ========================================
echo   职业规划师 - 后端服务启动
echo ========================================
echo.

cd /d "%~dp0"

REM 加载 .env 文件中的环境变量
if exist .env (
    for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
        set "line=%%a"
        if not "!line:~0,1!"=="#" (
            set "%%a=%%b"
        )
    )
)

python app.py
pause
