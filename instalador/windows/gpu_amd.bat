@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ==========================================
echo   Instalador Deep Live Cam - GPU AMD
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

:: Verificar se DirectML está disponível
echo ℹ️  DirectML é suportado nativamente no Windows 10/11
echo    Não é necessário instalar drivers adicionais.
echo    O DirectML funciona com GPUs AMD, Intel e NVIDIA.
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

:: Instalar dependências específicas para AMD DirectML
echo 📥 Instalando dependências para GPU AMD (DirectML)...
echo    Desinstalando ONNX Runtime padrão...
pip uninstall onnxruntime onnxruntime-directml -y
echo    Instalando ONNX Runtime DirectML...
pip install onnxruntime-directml==1.21.0
if errorlevel 1 (
    echo ❌ Erro ao instalar ONNX Runtime DirectML!
    echo    Tentando continuar com a instalação...
) else (
    echo ✅ ONNX Runtime DirectML instalado!
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

:: Modelo Face Swapper (FP16 funciona bem com DirectML)
if not exist "models\inswapper_128_fp16.onnx" (
    echo    Baixando inswapper_128_fp16.onnx (modelo GPU AMD)...
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri 'https://huggingface.co/hacksider/deep-live-cam/resolve/main/inswapper_128_fp16.onnx?download=true' -OutFile 'models\inswapper_128_fp16.onnx'}"
    if exist "models\inswapper_128_fp16.onnx" (
        echo ✅ Modelo Face Swapper (GPU) baixado com sucesso!
    ) else (
        echo ❌ Erro ao baixar modelo Face Swapper (GPU)
        echo    Tentando modelo alternativo (CPU)...
        powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri 'https://huggingface.co/hacksider/deep-live-cam/resolve/main/inswapper_128.onnx?download=true' -OutFile 'models\inswapper_128.onnx'}"
        if exist "models\inswapper_128.onnx" (
            echo ✅ Modelo Face Swapper (CPU) baixado como alternativa!
        ) else (
            echo ❌ Erro ao baixar modelos Face Swapper
            echo    Você pode baixar manualmente de:
            echo    https://huggingface.co/hacksider/deep-live-cam
        )
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
) else if exist "models\inswapper_128.onnx" (
    for %%A in ("models\inswapper_128.onnx") do echo ✅ inswapper_128.onnx - %%~zA bytes
) else (
    echo ❌ Modelo Face Swapper - NÃO ENCONTRADO
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
    echo    • Para executar: use run-directml.bat ou:
    echo      python run.py --execution-provider directml
    echo    • DirectML funciona nativamente no Windows 10/11
    echo    • Suporta GPUs AMD, Intel e NVIDIA
    echo    • Não requer drivers adicionais além dos drivers padrão da GPU
    echo.
    echo 🚀 Você já pode usar o Deep Live Cam com GPU AMD!
) else if exist "models\inswapper_128.onnx" (
    echo ✅ Instalação concluída com sucesso!
    echo.
    echo 💡 INFORMAÇÕES IMPORTANTES:
    echo    • Para executar: use run-directml.bat ou:
    echo      python run.py --execution-provider directml
    echo    • Modelo CPU instalado (funciona, mas pode ser mais lento)
    echo    • DirectML funciona nativamente no Windows 10/11
    echo.
    echo 🚀 Você já pode usar o Deep Live Cam!
) else (
    echo ⚠️  Instalação concluída, mas modelo principal não foi baixado.
    echo    Baixe manualmente de:
    echo    https://huggingface.co/hacksider/deep-live-cam
)
echo ==========================================
echo.
pause

