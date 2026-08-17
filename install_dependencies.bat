@echo off
echo ==========================================
echo Menginstal uv (Pengelola paket cepat Python)...
echo ==========================================
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

set "PATH=%USERPROFILE%\.local\bin;%USERPROFILE%\.cargo\bin;%PATH%"

echo.
echo ==========================================
echo Membuat virtual environment (.venv)...
echo ==========================================
uv venv

echo.
echo ==========================================
echo KONFIGURASI KARTU GRAFIS (GPU / VGA)
echo ==========================================
echo Apa jenis Kartu Grafis (VGA) Anda?
echo [1] NVIDIA (Dengan akselerasi CUDA - Jauh lebih cepat)
echo [2] AMD / Intel / CPU Biasa (Versi standar)
set /p gpu_choice="Pilihan Anda (1/2): "

if "%gpu_choice%"=="1" (
    echo.
    echo Menginstal PyTorch dan ONNX untuk NVIDIA (CUDA)...
    uv pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu124
    uv pip install onnxruntime-gpu==1.20.1
) else (
    echo.
    echo Menginstal PyTorch dan ONNX untuk AMD/CPU...
    uv pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cpu
    uv pip install onnxruntime==1.20.1
)

echo.
echo ==========================================
echo Menginstal dependensi utama dari requirements.txt...
echo ==========================================
uv pip install -r requirements.txt

echo.
echo ==========================================
echo Selesai! Semua dependensi berhasil diinstal.
echo ==========================================
pause
