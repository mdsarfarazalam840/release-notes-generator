@echo off
REM Load environment variables from .env file
for /f "usebackq tokens=1,2 delims==" %%a in (".env") do (
    if not "%%a"=="" if not "%%b"=="" (
        set %%a=%%b
    )
)
python run_enhanced_server.py
