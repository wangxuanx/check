@echo off
chcp 65001 >nul
REM ============================================================
REM  考勤处理工具 - Windows 一键打包脚本
REM  在任意 Windows 电脑上双击运行即可生成 .exe
REM ============================================================

echo ========================================
echo   考勤处理工具 Windows 打包脚本
echo ========================================
echo.

REM ---- 检查 Python ----
where python >nul 2>nul
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+ 并勾选 "Add to PATH"。
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] 安装依赖包……
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [错误] 依赖安装失败，请检查网络或 pip 配置。
    pause
    exit /b 1
)

echo.
echo [2/3] 开始打包（单文件、无控制台窗口）……
pyinstaller --noconfirm --onefile --windowed ^
    --name "考勤处理工具" ^
    --hidden-import xlrd ^
    --hidden-import xlwt ^
    --collect-submodules xlrd ^
    --collect-submodules xlwt ^
    app.py

if errorlevel 1 (
    echo [错误] 打包失败。
    pause
    exit /b 1
)

echo.
echo [3/3] 打包完成！
echo 生成的程序位于： dist\考勤处理工具.exe
echo.
echo 将该 exe 拷贝到任意 Windows 电脑即可直接双击运行，无需安装 Python。
echo.
pause
