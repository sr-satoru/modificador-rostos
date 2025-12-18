#!/bin/bash
# Script de instalação automática do servidor VPS
# Execute: bash install_vps.sh

echo "=========================================="
echo "Instalação do Servidor VPS - Deep Live Cam"
echo "=========================================="

# Verificar se é root
if [ "$EUID" -eq 0 ]; then 
   echo "❌ Não execute como root! Use um usuário normal."
   exit 1
fi

# Pedir path completo para instalação
echo ""
echo "📁 Onde você quer instalar o servidor?"
echo "   Exemplo: /home/usuario/Deep-live"
read -p "Digite o caminho completo: " INSTALL_PATH

# Validar path
if [ -z "$INSTALL_PATH" ]; then
    echo "❌ Caminho não pode ser vazio!"
    exit 1
fi

# Criar diretório se não existir
if [ ! -d "$INSTALL_PATH" ]; then
    echo "📁 Criando diretório: $INSTALL_PATH"
    mkdir -p "$INSTALL_PATH"
fi

# Ir para o diretório
cd "$INSTALL_PATH" || {
    echo "❌ Erro ao acessar diretório: $INSTALL_PATH"
    exit 1
}

echo "✅ Trabalhando em: $(pwd)"
echo ""

# Atualizar sistema
echo "📦 Atualizando sistema..."
sudo apt update && sudo apt upgrade -y

# Instalar dependências do sistema
echo "📦 Instalando dependências do sistema..."
sudo apt install -y python3 python3-pip python3-venv ffmpeg git wget curl

# Verificar Python
PYTHON_VERSION=$(python3 --version)
echo "✅ Python instalado: $PYTHON_VERSION"

# Verificar ffmpeg
FFMPEG_VERSION=$(ffmpeg -version | head -n 1)
echo "✅ FFmpeg instalado: $FFMPEG_VERSION"

# Criar ambiente virtual
echo "📦 Criando ambiente virtual em: $INSTALL_PATH/venv"
python3 -m venv venv

# Verificar se venv foi criado
if [ ! -d "venv" ]; then
    echo "❌ Erro ao criar ambiente virtual!"
    exit 1
fi

# Ativar ambiente virtual
echo "📦 Ativando ambiente virtual..."
source venv/bin/activate

# Atualizar pip
echo "📦 Atualizando pip..."
pip install --upgrade pip

# Instalar dependências
echo "📦 Instalando dependências Python..."
if [ -f "requirements_vps.txt" ]; then
    pip install -r requirements_vps.txt
else
    pip install websockets>=12.0 numpy opencv-python onnx insightface pillow onnxruntime-gpu tqdm
fi

# Verificar GPU NVIDIA (opcional)
if command -v nvidia-smi &> /dev/null; then
    echo "✅ GPU NVIDIA detectada:"
    nvidia-smi --query-gpu=name --format=csv,noheader
else
    echo "⚠️  GPU NVIDIA não detectada (usará CPU)"
fi

# Configurar firewall
echo "🔥 Configurando firewall..."
sudo ufw allow 8765/tcp
sudo ufw reload

# Criar pasta temp
echo "📁 Criando pastas necessárias..."
mkdir -p temp_vps
mkdir -p models

echo ""
echo "=========================================="
echo "✅ Instalação concluída!"
echo "=========================================="
echo ""
echo "📁 Instalado em: $INSTALL_PATH"
echo ""
echo "Próximos passos:"
echo "1. Baixe os modelos (se não tiver):"
echo "   cd $INSTALL_PATH/models/"
echo "   wget https://huggingface.co/hacksider/deep-live-cam/resolve/main/inswapper_128_fp16.onnx"
echo "   wget https://huggingface.co/hacksider/deep-live-cam/resolve/main/GFPGANv1.4.pth"
echo ""
echo "2. Ative o ambiente virtual:"
echo "   cd $INSTALL_PATH"
echo "   source venv/bin/activate"
echo ""
echo "3. Inicie o servidor:"
echo "   python modules/vps/server_ws.py"
echo ""
echo "4. Anote o IP da VPS para usar no cliente"
echo ""

