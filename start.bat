@echo off
chcp 65001 >nul
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
  py -3 -c "import lunar_python, pypinyin" >nul 2>nul || py -3 -m pip install -r requirements.txt
  start "" http://127.0.0.1:8000
  py -3 app.py
  goto :end
)

where python >nul 2>nul
if %errorlevel%==0 (
  python --version >nul 2>nul
  if %errorlevel%==0 (
    python -c "import lunar_python, pypinyin" >nul 2>nul || python -m pip install -r requirements.txt
    start "" http://127.0.0.1:8000
    python app.py
    goto :end
  )
)

echo [错误] 未检测到可用的 Python 3。
echo 请先从 https://www.python.org/downloads/ 安装 Python 3，安装时勾选 Add Python to PATH。
pause

:end
