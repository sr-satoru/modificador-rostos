#!/bin/bash

# Instalador Deep Live Cam - CPU Apenas
# Execute este script na pasta raiz do Deep-live

set -e

echo "=========================================="
echo "  Instalador Deep Live Cam - CPU Apenas"
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

echo "ℹ️  Este instalador configura o Deep Live Cam para funcionar APENAS com CPU."
echo "   Não é necessário ter GPU dedicada - funciona perfeitamente sem GPU!"
echo "   Será mais lento que com GPU, mas funciona perfeitamente."
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

# Instalar ONNX Runtime para CPU (remover GPU se existir)
echo "📥 Configurando ONNX Runtime para CPU..."
pip uninstall onnxruntime-gpu onnxruntime-directml -y 2>/dev/null || true
pip install onnxruntime
if [ $? -ne 0 ]; then
    echo "⚠️  Aviso: Erro ao instalar ONNX Runtime CPU. Continuando..."
else
    echo "✅ ONNX Runtime CPU instalado!"
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

# Modelo Face Swapper para CPU (obrigatório)
if [ ! -f "models/inswapper_128.onnx" ]; then
    echo "   Baixando inswapper_128.onnx (modelo CPU)..."
    if command -v wget &> /dev/null; then
        wget -O models/inswapper_128.onnx \
            "https://huggingface.co/hacksider/deep-live-cam/resolve/main/inswapper_128.onnx?download=true" \
            --progress=bar --show-progress 2>/dev/null || true
    elif command -v curl &> /dev/null; then
        curl -L -o models/inswapper_128.onnx \
            "https://huggingface.co/hacksider/deep-live-cam/resolve/main/inswapper_128.onnx?download=true" 2>/dev/null || true
    else
        echo "❌ wget ou curl não encontrado."
    fi
    
    if [ -f "models/inswapper_128.onnx" ]; then
        echo "✅ Modelo Face Swapper (CPU) baixado com sucesso!"
    else
        echo "⚠️  Modelo CPU não encontrado, tentando modelo FP16 (também funciona em CPU)..."
        if command -v wget &> /dev/null; then
            wget -O models/inswapper_128_fp16.onnx \
                "https://huggingface.co/hacksider/deep-live-cam/resolve/main/inswapper_128_fp16.onnx?download=true" \
                --progress=bar --show-progress 2>/dev/null || true
        elif command -v curl &> /dev/null; then
            curl -L -o models/inswapper_128_fp16.onnx \
                "https://huggingface.co/hacksider/deep-live-cam/resolve/main/inswapper_128_fp16.onnx?download=true" 2>/dev/null || true
        fi
        
        if [ -f "models/inswapper_128_fp16.onnx" ]; then
            echo "✅ Modelo Face Swapper (FP16) baixado - funciona em CPU também!"
        else
            echo "❌ Erro ao baixar modelo Face Swapper"
            echo "   Você pode baixar manualmente de:"
            echo "   https://huggingface.co/hacksider/deep-live-cam"
        fi
    fi
else
    echo "✅ Modelo inswapper_128.onnx já existe"
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
if [ -f "models/inswapper_128.onnx" ]; then
    SIZE=$(du -h models/inswapper_128.onnx | cut -f1)
    echo "✅ inswapper_128.onnx (CPU) - $SIZE"
elif [ -f "models/inswapper_128_fp16.onnx" ]; then
    SIZE=$(du -h models/inswapper_128_fp16.onnx | cut -f1)
    echo "✅ inswapper_128_fp16.onnx (também funciona em CPU) - $SIZE"
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
if [ -f "models/inswapper_128.onnx" ]; then
    echo "✅ Instalação concluída com sucesso!"
    echo ""
    echo "💡 INFORMAÇÕES IMPORTANTES:"
    echo "   • O sistema FUNCIONA SEM GPU DEDICADA usando CPU"
    echo "   • Será mais lento, mas funciona perfeitamente"
    echo "   • Para executar: python run.py"
    echo "   • O sistema detecta automaticamente e usa CPU"
    echo "   • Para CPU: usa inswapper_128.onnx (otimizado)"
    echo ""
    echo "🚀 Você já pode usar o Deep Live Cam sem GPU!"
elif [ -f "models/inswapper_128_fp16.onnx" ]; then
    echo "✅ Instalação concluída com sucesso!"
    echo ""
    echo "💡 INFORMAÇÕES IMPORTANTES:"
    echo "   • O sistema FUNCIONA SEM GPU DEDICADA usando CPU"
    echo "   • Será mais lento, mas funciona perfeitamente"
    echo "   • Para executar: python run.py"
    echo "   • O modelo FP16 também funciona em CPU (mais lento)"
    echo ""
    echo "🚀 Você já pode usar o Deep Live Cam sem GPU!"
else
    echo "⚠️  Instalação concluída, mas modelo principal não foi baixado."
    echo "   Baixe manualmente de:"
    echo "   https://huggingface.co/hacksider/deep-live-cam"
fi
echo "=========================================="
echo ""

