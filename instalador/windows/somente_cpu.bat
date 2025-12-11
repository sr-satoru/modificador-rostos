@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ==========================================
echo   Instalador Deep Live Cam - CPU Apenas
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

:: Obter diretório do script
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%\.."
set "ROOT_DIR=%CD%"

echo 📁 Diretório de instalação: %ROOT_DIR%
echo.

echo ℹ️  Este instalador configura o Deep Live Cam para funcionar APENAS com CPU.
echo    Não é necessário ter GPU dedicada - funciona perfeitamente sem GPU!
echo    Será mais lento que com GPU, mas funciona perfeitamente.
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

:: Instalar ONNX Runtime para CPU (remover GPU se existir)
echo 📥 Configurando ONNX Runtime para CPU...
pip uninstall onnxruntime-gpu onnxruntime-directml -y
pip install onnxruntime
if errorlevel 1 (
    echo ⚠️  Aviso: Erro ao instalar ONNX Runtime CPU. Continuando...
) else (
    echo ✅ ONNX Runtime CPU instalado!
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

:: Modelo Face Swapper para CPU (obrigatório)
if not exist "models\inswapper_128.onnx" (
    echo    Baixando inswapper_128.onnx (modelo CPU)...
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri 'https://huggingface.co/hacksider/deep-live-cam/resolve/main/inswapper_128.onnx?download=true' -OutFile 'models\inswapper_128.onnx'}"
    if exist "models\inswapper_128.onnx" (
        echo ✅ Modelo Face Swapper (CPU) baixado com sucesso!
    ) else (
        echo ⚠️  Modelo CPU não encontrado, tentando modelo FP16 (também funciona em CPU)...
        powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri 'https://huggingface.co/hacksider/deep-live-cam/resolve/main/inswapper_128_fp16.onnx?download=true' -OutFile 'models\inswapper_128_fp16.onnx'}"
        if exist "models\inswapper_128_fp16.onnx" (
            echo ✅ Modelo Face Swapper (FP16) baixado - funciona em CPU também!
        ) else (
            echo ❌ Erro ao baixar modelo Face Swapper
            echo    Você pode baixar manualmente de:
            echo    https://huggingface.co/hacksider/deep-live-cam
        )
    )
) else (
    echo ✅ Modelo inswapper_128.onnx já existe
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
if exist "models\inswapper_128.onnx" (
    for %%A in ("models\inswapper_128.onnx") do echo ✅ inswapper_128.onnx (CPU) - %%~zA bytes
) else if exist "models\inswapper_128_fp16.onnx" (
    for %%A in ("models\inswapper_128_fp16.onnx") do echo ✅ inswapper_128_fp16.onnx (também funciona em CPU) - %%~zA bytes
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
if exist "models\inswapper_128.onnx" (
    echo ✅ Instalação concluída com sucesso!
    echo.
    echo 💡 INFORMAÇÕES IMPORTANTES:
    echo    • O sistema FUNCIONA SEM GPU DEDICADA usando CPU
    echo    • Será mais lento, mas funciona perfeitamente
    echo    • Para executar: python run.py
    echo    • O sistema detecta automaticamente e usa CPU
    echo    • Para CPU: usa inswapper_128.onnx (otimizado)
    echo.
    echo 🚀 Você já pode usar o Deep Live Cam sem GPU!
) else if exist "models\inswapper_128_fp16.onnx" (
    echo ✅ Instalação concluída com sucesso!
    echo.
    echo 💡 INFORMAÇÕES IMPORTANTES:
    echo    • O sistema FUNCIONA SEM GPU DEDICADA usando CPU
    echo    • Será mais lento, mas funciona perfeitamente
    echo    • Para executar: python run.py
    echo    • O modelo FP16 também funciona em CPU (mais lento)
    echo.
    echo 🚀 Você já pode usar o Deep Live Cam sem GPU!
) else (
    echo ⚠️  Instalação concluída, mas modelo principal não foi baixado.
    echo    Baixe manualmente de:
    echo    https://huggingface.co/hacksider/deep-live-cam
)
echo ==========================================
echo.
pause

