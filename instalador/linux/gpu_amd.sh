#!/bin/bash

# Instalador Deep Live Cam - GPU AMD (DirectML)
# Execute este script na pasta raiz do Deep-live
# Nota: DirectML é específico do Windows. Em Linux, use ROCm ou CPU.

set -e

echo "=========================================="
echo "  Instalador Deep Live Cam - GPU AMD"
echo "=========================================="
echo ""

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ Python não encontrado!"
    echo "   Por favor, instale Python 3.11 ou superior"
    exit 1
fi

# Usar python3 se disponível, senão python
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

echo "✅ Python encontrado"
$PYTHON_CMD --version
echo ""

# Obter diretório do script e navegar para a raiz do Deep-live
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$ROOT_DIR"

echo "📁 Diretório de instalação: $ROOT_DIR"
echo ""

# Aviso sobre DirectML (Windows apenas)
if [[ "$OSTYPE" != "msys" && "$OSTYPE" != "win32" && "$OSTYPE" != "cygwin" ]]; then
    echo "⚠️  AVISO: DirectML é específico do Windows."
    echo "   Em Linux, você pode usar:"
    echo "   • CPU (somente_cpu.sh)"
    echo "   • ROCm (se disponível)"
    echo ""
    echo "   Continuando com instalação para CPU (funciona, mas mais lento)..."
    echo ""
    read -p "   Deseja continuar? (S/N): " CONTINUE
    if [[ ! "$CONTINUE" =~ ^[Ss]$ ]]; then
        echo "Instalação cancelada."
        exit 0
    fi
    USE_CPU_FALLBACK=true
else
    echo "ℹ️  DirectML é suportado nativamente no Windows 10/11"
    echo "   Não é necessário instalar drivers adicionais."
    echo "   O DirectML funciona com GPUs AMD, Intel e NVIDIA."
    echo ""
    USE_CPU_FALLBACK=false
fi

# Criar ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo "📦 Criando ambiente virtual..."
    $PYTHON_CMD -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Erro ao criar ambiente virtual!"
        exit 1
    fi
    echo "✅ Ambiente virtual criado!"
else
    echo "✅ Ambiente virtual já existe"
fi
echo ""

# Ativar ambiente virtual
echo "🔄 Ativando ambiente virtual..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "❌ Erro ao ativar ambiente virtual!"
    exit 1
fi
echo "✅ Ambiente virtual ativado!"
echo ""

# Atualizar pip
echo "📥 Atualizando pip..."
pip install --upgrade pip
echo ""

# Instalar dependências base
echo "📥 Instalando dependências base..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Erro ao instalar dependências base!"
    exit 1
fi
echo "✅ Dependências base instaladas!"
echo ""

# Instalar dependências específicas para AMD DirectML (ou CPU em Linux)
if [ "$USE_CPU_FALLBACK" = true ]; then
    echo "📥 Configurando para CPU (DirectML não disponível em Linux)..."
    pip uninstall onnxruntime-directml -y 2>/dev/null || true
    pip install onnxruntime
    echo "✅ ONNX Runtime CPU instalado!"
else
    echo "📥 Instalando dependências para GPU AMD (DirectML)..."
    echo "   Desinstalando ONNX Runtime padrão..."
    pip uninstall onnxruntime onnxruntime-directml -y
    echo "   Instalando ONNX Runtime DirectML..."
    pip install onnxruntime-directml==1.21.0
    if [ $? -ne 0 ]; then
        echo "❌ Erro ao instalar ONNX Runtime DirectML!"
        echo "   Tentando continuar com a instalação..."
    else
        echo "✅ ONNX Runtime DirectML instalado!"
    fi
fi
echo ""

# Criar diretório de modelos se não existir
if [ ! -d "models" ]; then
    mkdir -p models
    echo "✅ Diretório 'models' criado!"
fi

# Baixar modelos
echo "📥 Baixando modelos necessários..."
echo ""

# Modelo Face Swapper (FP16 funciona bem com DirectML)
if [ ! -f "models/inswapper_128_fp16.onnx" ]; then
    echo "   Baixando inswapper_128_fp16.onnx (modelo GPU AMD)..."
    if command -v wget &> /dev/null; then
        wget -O models/inswapper_128_fp16.onnx \
            "https://huggingface.co/hacksider/deep-live-cam/resolve/main/inswapper_128_fp16.onnx?download=true" \
            --progress=bar --show-progress 2>/dev/null || true
    elif command -v curl &> /dev/null; then
        curl -L -o models/inswapper_128_fp16.onnx \
            "https://huggingface.co/hacksider/deep-live-cam/resolve/main/inswapper_128_fp16.onnx?download=true" 2>/dev/null || true
    else
        echo "❌ wget ou curl não encontrado."
    fi
    
    if [ -f "models/inswapper_128_fp16.onnx" ]; then
        echo "✅ Modelo Face Swapper (GPU) baixado com sucesso!"
    else
        echo "❌ Erro ao baixar modelo Face Swapper (GPU)"
        echo "   Tentando modelo alternativo (CPU)..."
        if command -v wget &> /dev/null; then
            wget -O models/inswapper_128.onnx \
                "https://huggingface.co/hacksider/deep-live-cam/resolve/main/inswapper_128.onnx?download=true" \
                --progress=bar --show-progress 2>/dev/null || true
        elif command -v curl &> /dev/null; then
            curl -L -o models/inswapper_128.onnx \
                "https://huggingface.co/hacksider/deep-live-cam/resolve/main/inswapper_128.onnx?download=true" 2>/dev/null || true
        fi
        
        if [ -f "models/inswapper_128.onnx" ]; then
            echo "✅ Modelo Face Swapper (CPU) baixado como alternativa!"
        else
            echo "❌ Erro ao baixar modelos Face Swapper"
            echo "   Você pode baixar manualmente de:"
            echo "   https://huggingface.co/hacksider/deep-live-cam"
        fi
    fi
else
    echo "✅ Modelo inswapper_128_fp16.onnx já existe"
fi
echo ""

# Modelo Face Enhancer (opcional, mas recomendado)
if [ ! -f "models/GFPGANv1.4.pth" ]; then
    echo "   Baixando GFPGANv1.4.pth (Face Enhancer - opcional)..."
    if command -v wget &> /dev/null; then
        wget -O models/GFPGANv1.4.pth \
            "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.4/GFPGANv1.4.pth" \
            --progress=bar --show-progress 2>/dev/null || true
    elif command -v curl &> /dev/null; then
        curl -L -o models/GFPGANv1.4.pth \
            "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.4/GFPGANv1.4.pth" 2>/dev/null || true
    else
        echo "❌ wget ou curl não encontrado."
    fi
    
    if [ -f "models/GFPGANv1.4.pth" ]; then
        echo "✅ Modelo Face Enhancer baixado com sucesso!"
    else
        echo "⚠️  Aviso: Não foi possível baixar Face Enhancer (opcional)"
        echo "   Você pode baixar manualmente de:"
        echo "   https://github.com/TencentARC/GFPGAN/releases/download/v1.3.4/GFPGANv1.4.pth"
    fi
else
    echo "✅ Modelo GFPGANv1.4.pth já existe"
fi
echo ""

# Verificar arquivos baixados
echo "=========================================="
echo "  Verificando arquivos baixados..."
echo "=========================================="
if [ -f "models/inswapper_128_fp16.onnx" ]; then
    SIZE=$(du -h models/inswapper_128_fp16.onnx | cut -f1)
    echo "✅ inswapper_128_fp16.onnx - $SIZE"
elif [ -f "models/inswapper_128.onnx" ]; then
    SIZE=$(du -h models/inswapper_128.onnx | cut -f1)
    echo "✅ inswapper_128.onnx - $SIZE"
else
    echo "❌ Modelo Face Swapper - NÃO ENCONTRADO"
fi

if [ -f "models/GFPGANv1.4.pth" ]; then
    SIZE=$(du -h models/GFPGANv1.4.pth | cut -f1)
    echo "✅ GFPGANv1.4.pth - $SIZE"
else
    echo "⚠️  GFPGANv1.4.pth - NÃO ENCONTRADO (opcional)"
fi
echo ""

# Mensagem final
echo "=========================================="
if [ -f "models/inswapper_128_fp16.onnx" ]; then
    echo "✅ Instalação concluída com sucesso!"
    echo ""
    if [ "$USE_CPU_FALLBACK" = true ]; then
        echo "💡 INFORMAÇÕES IMPORTANTES:"
        echo "   • Instalado para CPU (DirectML não disponível em Linux)"
        echo "   • Para executar: python run.py"
        echo "   • O sistema detecta automaticamente e usa CPU"
        echo ""
        echo "🚀 Você já pode usar o Deep Live Cam!"
    else
        echo "💡 INFORMAÇÕES IMPORTANTES:"
        echo "   • Para executar: python run.py --execution-provider directml"
        echo "   • DirectML funciona nativamente no Windows 10/11"
        echo "   • Suporta GPUs AMD, Intel e NVIDIA"
        echo "   • Não requer drivers adicionais além dos drivers padrão da GPU"
        echo ""
        echo "🚀 Você já pode usar o Deep Live Cam com GPU AMD!"
    fi
elif [ -f "models/inswapper_128.onnx" ]; then
    echo "✅ Instalação concluída com sucesso!"
    echo ""
    echo "💡 INFORMAÇÕES IMPORTANTES:"
    if [ "$USE_CPU_FALLBACK" = true ]; then
        echo "   • Instalado para CPU (DirectML não disponível em Linux)"
    else
        echo "   • Modelo CPU instalado (funciona, mas pode ser mais lento)"
        echo "   • DirectML funciona nativamente no Windows 10/11"
    fi
    echo "   • Para executar: python run.py"
    echo ""
    echo "🚀 Você já pode usar o Deep Live Cam!"
else
    echo "⚠️  Instalação concluída, mas modelo principal não foi baixado."
    echo "   Baixe manualmente de:"
    echo "   https://huggingface.co/hacksider/deep-live-cam"
fi
echo "=========================================="
echo ""

