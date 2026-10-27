@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo [!] Python not found. Install Python 3.10 or 3.11 from https://www.python.org and tick "Add to PATH".
  goto :fail
)

if not exist ".venv\Scripts\python.exe" (
  echo [1/4] Creating virtual environment .venv
  python -m venv .venv || goto :fail
)
set "PY=.venv\Scripts\python.exe"
"%PY%" -m pip install --upgrade pip -q

echo [2/4] Installing PyTorch with CUDA 12.6 (about 2.9 GB, may take a while)
set "TORCH_WHL="
for %%F in ("wheels\torch-2.8.0+cu126-*.whl") do set "TORCH_WHL=%%~F"
if defined TORCH_WHL (
  echo       using local file %TORCH_WHL%
  "%PY%" -m pip install "%TORCH_WHL%" torchaudio==2.8.0 --extra-index-url https://download.pytorch.org/whl/cu126 || goto :fail
) else (
  "%PY%" -m pip install torch==2.8.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cu126 || goto :fail
)

echo [3/4] Installing the other packages
"%PY%" -m pip install -r requirements.txt -c constraints.txt --extra-index-url https://download.pytorch.org/whl/cu126 || goto :fail
rem torchcodec needs FFmpeg DLLs and is not used; removing it avoids load errors
"%PY%" -m pip uninstall -y -q torchcodec >nul 2>nul

echo [4/4] Checking the install
"%PY%" -c "import torch, f5_tts, gradio, edge_tts, faster_whisper; print('  PyTorch', torch.__version__, '| GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'none (CPU mode, slow)')" || goto :fail

echo.
echo Done! Double-click start.bat to open the app.
echo The Thai model (about 1.3 GB) downloads the first time it starts.
if not defined NOPAUSE pause
exit /b 0

:fail
echo.
echo [!] Setup failed. See the messages above.
if not defined NOPAUSE pause
exit /b 1
