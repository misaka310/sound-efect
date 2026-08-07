@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 goto no_python
py -3 -m venv .venv
if errorlevel 1 goto venv_error
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
if errorlevel 1 goto pip_error
nvidia-smi >nul 2>nul
if errorlevel 1 goto no_gpu
pip install -r requirements.txt
if errorlevel 1 goto deps_error
echo Installing CUDA PyTorch (CPU fallback is disabled)...
pip install --force-reinstall torch==2.7.1+cu128 torchaudio==2.7.1+cu128 --index-url https://download.pytorch.org/whl/cu128
if errorlevel 1 goto torch_error
echo Setup complete. Accept both Hugging Face model licenses, then run: hf auth login
exit /b 0
:no_python
echo ERROR: Install Python 3.10 through 3.13 and enable PATH.
exit /b 1
:venv_error
echo ERROR: Could not create .venv.
exit /b 1
:pip_error
echo ERROR: pip upgrade failed. Check network access.
exit /b 1
:no_gpu
echo ERROR: NVIDIA GPU was not detected. CPU fallback is disabled; check nvidia-smi and the driver.
exit /b 1
:torch_error
echo ERROR: CUDA PyTorch installation failed. See https://pytorch.org/get-started/locally/
exit /b 1
:deps_error
echo ERROR: Application dependency installation failed. Read the package error above.
exit /b 1
