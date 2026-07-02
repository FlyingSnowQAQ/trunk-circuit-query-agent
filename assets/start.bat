@echo off
chcp 65001 >nul
title 移动干线电路查询智能体

setlocal

echo ============================================
echo   📡 移动干线电路查询智能体 - 启动中...
echo ============================================
echo.

:: 检查 Python 环境
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [✗] 未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

:: 切换到项目目录
cd /d "%~dp0"

:: 修复 PYTHONPATH 冲突（清理环境变量）
set PYTHONHOME=
set PYTHONPATH=

:: 检查依赖
echo [1/4] 检查 Python 依赖...
python -c "import fastapi, uvicorn, httpx, jinja2" >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] 安装依赖中...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [✗] 依赖安装失败，请手动执行: pip install -r requirements.txt
        pause
        exit /b 1
    )
)
echo [✓] 依赖检查通过

:: 检查数据库
echo [2/4] 检查数据库文件...
if not exist "%USERPROFILE%\WorkBuddy\2026-06-17-15-28-15\circuit-query-system\output\circuits.db" (
    echo [!] 数据库文件未找到！
    echo     匹配路径: %USERPROFILE%\WorkBuddy\2026-06-17-15-28-15\circuit-query-system\output\circuits.db
    echo.
    echo     请先运行 circuit-query-system 的 preprocess.py 构建数据库
    echo     或设置环境变量 CIRCUIT_DB_PATH 指定数据库路径
    echo.
    pause
    exit /b 1
)
echo [✓] 数据库文件已存在

:: DeepSeek API 配置提示
echo [3/4] 检查 DeepSeek API 配置...
if "%DEEPSEEK_API_KEY%"=="" (
    echo [!] 未设置 DEEPSEEK_API_KEY 环境变量
    echo     系统将以降级模式运行（纯SQL查询，无AI总结）
    echo     如需启用AI总结，请设置:
    echo     set DEEPSEEK_API_KEY=your_api_key
    echo.
) else (
    echo [✓] DeepSeek API 已配置
)

:: 启动服务
echo [4/4] 启动 API 服务...
echo.
echo    🌐 访问地址: http://localhost:8000
echo    📋 健康检查: http://localhost:8000/api/health
echo    💡 按 Ctrl+C 停止服务
echo.
echo ============================================

python -m api.server

pause
