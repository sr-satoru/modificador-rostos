@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ==========================================
echo   Instalador Deep Live Cam - GPU NVIDIA
echo ==========================================
echo.

:: Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado!
    echo    Por favor, instale Python 3.11 ou superior de https://www.python.org/
    echo    Certifique-se de marcar "Add Python to PATH" durante a instalação.
    pause
    exit /b 1
)

echo ✅ Python encontrado
python --version
echo.

:: Obter diretório do script e navegar para a raiz do Deep-live
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%\.."
set "ROOT_DIR=%CD%"

echo 📁 Diretório de instalação: %ROOT_DIR%
echo.

:: Verificar se CUDA está instalado (opcional, mas recomendado)
echo ⚠️  IMPORTANTE: Para usar GPU NVIDIA, você precisa ter:
echo    • CUDA Toolkit 12.8.0 instalado
echo    • cuDNN v8.9.7 para CUDA 12.x instalado
echo    • Ambos adicionados ao PATH do sistema
echo.
echo    Se não tiver CUDA instalado, o sistema funcionará em CPU (mais lento).
echo    Deseja continuar mesmo assim? (S/N)
set /p CONTINUE="> "
if /i not "%CONTINUE%"=="S" (
    echo Instalação cancelada.
    pause
    exit /b 0
)
echo.

:: Criar ambiente virtual se não existir
if not exist "venv" (
    echo 📦 Criando ambiente virtual...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Erro ao criar ambiente virtual!
        pause
        exit /b 1
    )
    echo ✅ Ambiente virtual criado!
) else (
    echo ✅ Ambiente virtual já existe
)
echo.

:: Ativar ambiente virtual
echo 🔄 Ativando ambiente virtual...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Erro ao ativar ambiente virtual!
    pause
    exit /b 1
)
echo ✅ Ambiente virtual ativado!
echo.

:: Atualizar pip
echo 📥 Atualizando pip...
python -m pip install --upgrade pip
echo.

:: Instalar dependências base
echo 📥 Instalando dependências base...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Erro ao instalar dependências base!
    pause
    exit /b 1
)
echo ✅ Dependências base instaladas!
echo.

:: Instalar dependências específicas para NVIDIA CUDA
echo 📥 Instalando dependências para GPU NVIDIA (CUDA)...
echo    Instalando PyTorch com suporte CUDA 12.8...
pip install -U torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
if errorlevel 1 (
    echo ⚠️  Aviso: Erro ao instalar PyTorch com CUDA. Continuando...
) else (
    echo ✅ PyTorch com CUDA instalado!
)

echo    Instalando ONNX Runtime GPU...
pip uninstall onnxruntime onnxruntime-gpu -y
pip install onnxruntime-gpu==1.21.0
if errorlevel 1 (
    echo ⚠️  Aviso: Erro ao instalar ONNX Runtime GPU. Continuando...
) else (
    echo ✅ ONNX Runtime GPU instalado!
)
echo.

:: Criar diretório de modelos se não existir
if not exist "models" (
    mkdir models
    echo ✅ Diretório 'models' criado!
)

:: Baixar modelos usando PowerShell
echo 📥 Baixando modelos necessários...
echo.

:: Modelo Face Swapper para GPU (FP16)
if not exist "models\inswapper_128_fp16.onnx" (
    echo    Baixando inswapper_128_fp16.onnx (modelo GPU NVIDIA)...
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri 'https://huggingface.co/hacksider/deep-live-cam/resolve/main/inswapper_128_fp16.onnx?download=true' -OutFile 'models\inswapper_128_fp16.onnx'}"
    if exist "models\inswapper_128_fp16.onnx" (
        echo ✅ Modelo Face Swapper (GPU) baixado com sucesso!
    ) else (
        echo ❌ Erro ao baixar modelo Face Swapper (GPU)
        echo    Você pode baixar manualmente de:
        echo    https://huggingface.co/hacksider/deep-live-cam/resolve/main/inswapper_128_fp16.onnx
    )
) else (
    echo ✅ Modelo inswapper_128_fp16.onnx já existe
)
echo.

:: Modelo Face Enhancer (opcional, mas recomendado)
if not exist "models\GFPGANv1.4.pth" (
    echo    Baixando GFPGANv1.4.pth (Face Enhancer - opcional)...
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri 'https://github.com/TencentARC/GFPGAN/releases/download/v1.3.4/GFPGANv1.4.pth' -OutFile 'models\GFPGANv1.4.pth'}"
    if exist "models\GFPGANv1.4.pth" (
        echo ✅ Modelo Face Enhancer baixado com sucesso!
    ) else (
        echo ⚠️  Aviso: Não foi possível baixar Face Enhancer (opcional)
        echo    Você pode baixar manualmente de:
        echo    https://github.com/TencentARC/GFPGAN/releases/download/v1.3.4/GFPGANv1.4.pth
    )
) else (
    echo ✅ Modelo GFPGANv1.4.pth já existe
)
echo.

:: Verificar arquivos baixados
echo ==========================================
echo   Verificando arquivos baixados...
echo ==========================================
if exist "models\inswapper_128_fp16.onnx" (
    for %%A in ("models\inswapper_128_fp16.onnx") do echo ✅ inswapper_128_fp16.onnx - %%~zA bytes
) else (
    echo ❌ inswapper_128_fp16.onnx - NÃO ENCONTRADO
)

if exist "models\GFPGANv1.4.pth" (
    for %%A in ("models\GFPGANv1.4.pth") do echo ✅ GFPGANv1.4.pth - %%~zA bytes
) else (
    echo ⚠️  GFPGANv1.4.pth - NÃO ENCONTRADO (opcional)
)
echo.

:: Mensagem final
echo ==========================================
if exist "models\inswapper_128_fp16.onnx" (
    echo ✅ Instalação concluída com sucesso!
    echo.
    echo 💡 INFORMAÇÕES IMPORTANTES:
    echo    • Para executar: use run-cuda.bat ou:
    echo      python run.py --execution-provider cuda
    echo    • Certifique-se de ter CUDA Toolkit 12.8.0 e cuDNN instalados
    echo    • Se CUDA não estiver disponível, funcionará em CPU (mais lento)
    echo.
    echo 🚀 Você já pode usar o Deep Live Cam com GPU NVIDIA!
) else (
    echo ⚠️  Instalação concluída, mas modelo principal não foi baixado.
    echo    Baixe manualmente de:
    echo    https://huggingface.co/hacksider/deep-live-cam
)
echo ==========================================
echo.
pause

