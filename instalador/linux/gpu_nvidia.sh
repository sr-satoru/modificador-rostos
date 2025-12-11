#!/bin/bash

# Instalador Deep Live Cam - GPU NVIDIA
# Execute este script na pasta raiz do Deep-live

set -e

echo "=========================================="
echo "  Instalador Deep Live Cam - GPU NVIDIA"
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

# Verificar se CUDA está instalado (opcional, mas recomendado)
echo "⚠️  IMPORTANTE: Para usar GPU NVIDIA, você precisa ter:"
echo "   • CUDA Toolkit 12.8.0 instalado"
echo "   • cuDNN v8.9.7 para CUDA 12.x instalado"
echo "   • Ambos adicionados ao PATH do sistema"
echo ""
echo "   Se não tiver CUDA instalado, o sistema funcionará em CPU (mais lento)."
read -p "   Deseja continuar mesmo assim? (S/N): " CONTINUE
if [[ ! "$CONTINUE" =~ ^[Ss]$ ]]; then
    echo "Instalação cancelada."
    exit 0
fi
echo ""

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

# Instalar dependências específicas para NVIDIA CUDA
echo "📥 Instalando dependências para GPU NVIDIA (CUDA)..."
echo "   Instalando PyTorch com suporte CUDA 12.8..."
pip install -U torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
if [ $? -ne 0 ]; then
    echo "⚠️  Aviso: Erro ao instalar PyTorch com CUDA. Continuando..."
else
    echo "✅ PyTorch com CUDA instalado!"
fi

echo "   Instalando ONNX Runtime GPU..."
pip uninstall onnxruntime onnxruntime-gpu -y
pip install onnxruntime-gpu==1.21.0
if [ $? -ne 0 ]; then
    echo "⚠️  Aviso: Erro ao instalar ONNX Runtime GPU. Continuando..."
else
    echo "✅ ONNX Runtime GPU instalado!"
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

# Modelo Face Swapper para GPU (FP16)
if [ ! -f "models/inswapper_128_fp16.onnx" ]; then
    echo "   Baixando inswapper_128_fp16.onnx (modelo GPU NVIDIA)..."
    if command -v wget &> /dev/null; then
        wget -O models/inswapper_128_fp16.onnx \
            "https://huggingface.co/hacksider/deep-live-cam/resolve/main/inswapper_128_fp16.onnx?download=true" \
            --progress=bar --show-progress 2>/dev/null || true
    elif command -v curl &> /dev/null; then
        curl -L -o models/inswapper_128_fp16.onnx \
            "https://huggingface.co/hacksider/deep-live-cam/resolve/main/inswapper_128_fp16.onnx?download=true" 2>/dev/null || true
    else
        echo "❌ wget ou curl não encontrado. Instale um deles para baixar modelos."
    fi
    
    if [ -f "models/inswapper_128_fp16.onnx" ]; then
        echo "✅ Modelo Face Swapper (GPU) baixado com sucesso!"
    else
        echo "❌ Erro ao baixar modelo Face Swapper (GPU)"
        echo "   Você pode baixar manualmente de:"
        echo "   https://huggingface.co/hacksider/deep-live-cam/resolve/main/inswapper_128_fp16.onnx"
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
else
    echo "❌ inswapper_128_fp16.onnx - NÃO ENCONTRADO"
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
    echo "💡 INFORMAÇÕES IMPORTANTES:"
    echo "   • Para executar: python run.py --execution-provider cuda"
    echo "   • Certifique-se de ter CUDA Toolkit 12.8.0 e cuDNN instalados"
    echo "   • Se CUDA não estiver disponível, funcionará em CPU (mais lento)"
    echo ""
    echo "🚀 Você já pode usar o Deep Live Cam com GPU NVIDIA!"
else
    echo "⚠️  Instalação concluída, mas modelo principal não foi baixado."
    echo "   Baixe manualmente de:"
    echo "   https://huggingface.co/hacksider/deep-live-cam"
fi
echo "=========================================="
echo ""

