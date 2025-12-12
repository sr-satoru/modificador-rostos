# 🎭 DEEP FACE by Satoru Gojo

<div align="center">

**Troca de rosto em tempo real com IA - Simples, Rápido e Poderoso**

*Transforme qualquer rosto em tempo real com apenas uma imagem*

</div>

---

## 📌 Créditos ao Projeto Original

Este projeto é uma modificação e melhoria do projeto original:

**🔗 [Deep-Live-Cam](https://github.com/hacksider/Deep-Live-Cam)** por [@hacksider](https://github.com/hacksider)

O sistema de instalação automatizado foi desenvolvido como uma melhoria sobre o projeto original, adicionando instaladores dedicados para diferentes configurações de GPU (NVIDIA, AMD) e CPU, simplificando significativamente o processo de instalação.

---

## 📋 Sobre o Projeto

**DEEP FACE** é uma ferramenta avançada de deepfake em tempo real que permite trocar rostos em vídeos, imagens e até mesmo em transmissões ao vivo usando apenas uma foto de referência. Desenvolvido com tecnologia de ponta em IA, o sistema oferece resultados impressionantes com processamento rápido e eficiente.

### ✨ Características Principais

- 🎥 **Processamento em Tempo Real**: Troca de rosto ao vivo via webcam
- 🖼️ **Suporte a Imagens e Vídeos**: Processe arquivos estáticos ou dinâmicos
- ⚡ **Aceleração por GPU**: Suporte completo para NVIDIA CUDA e AMD DirectML
- 💻 **Funciona sem GPU**: Processamento via CPU para qualquer computador
- 🎨 **Interface Intuitiva**: Interface gráfica simples e fácil de usar
- 🔧 **Instaladores Automáticos**: Sistema de instalação simplificado para todos os cenários

---

## 🚀 Instalação Rápida

O **DEEP FACE** possui um sistema de instalação automatizado que detecta sua configuração e instala tudo automaticamente. Escolha o instalador correto para seu sistema:

### 📦 Instaladores Disponíveis

#### 🪟 Windows

Todos os instaladores estão na pasta `instalador/windows/`:

- **`gpu_nvidia.bat`** - Para GPUs NVIDIA (CUDA)
- **`gpu_amd.bat`** - Para GPUs AMD (DirectML)
- **`somente_cpu.bat`** - Para processamento apenas com CPU

#### 🐧 Linux

Todos os instaladores estão na pasta `instalador/linux/`:

- **`gpu_nvidia.sh`** - Para GPUs NVIDIA (CUDA)
- **`gpu_amd.sh`** - Para GPUs AMD (com fallback para CPU)
- **`somente_cpu.sh`** - Para processamento apenas com CPU

---

## 📖 Guia de Instalação Detalado

### 🔧 Pré-requisitos

Antes de começar, certifique-se de ter instalado:

- **Python 3.11 ou superior** ([Download](https://www.python.org/downloads/))
- **pip** (geralmente vem com Python)
- **Git** (opcional, apenas se for clonar o repositório)

### 🪟 Instalação no Windows

#### Opção 1: Instalador Automático (Recomendado)

1. **Navegue até a pasta do projeto:**
   ```cmd
   cd Deep-live
   ```

2. **Escolha e execute o instalador apropriado:**

   **Para GPU NVIDIA:**
   ```cmd
   instalador\windows\gpu_nvidia.bat
   ```

   **Para GPU AMD:**
   ```cmd
   instalador\windows\gpu_amd.bat
   ```

   **Para CPU apenas:**
   ```cmd
   instalador\windows\somente_cpu.bat
   ```

3. **Aguarde a instalação completa** - O script irá:
   - Verificar se Python está instalado
   - Criar ambiente virtual automaticamente
   - Instalar todas as dependências
   - Baixar os modelos necessários

#### Opção 2: Instalação Manual

**Criando Ambiente Virtual no Windows:**

```cmd
# Navegue até a pasta do projeto
cd Deep-live

# Crie o ambiente virtual
python -m venv venv

# Ative o ambiente virtual
venv\Scripts\activate

# Atualize o pip
python -m pip install --upgrade pip

# Instale as dependências
pip install -r requirements.txt
```

**Para GPU NVIDIA (após instalação base):**
```cmd
# Instale PyTorch com CUDA
pip install -U torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# Instale ONNX Runtime GPU
pip uninstall onnxruntime onnxruntime-gpu -y
pip install onnxruntime-gpu==1.21.0
```

**Para GPU AMD (após instalação base):**
```cmd
# Instale ONNX Runtime DirectML
pip uninstall onnxruntime onnxruntime-directml -y
pip install onnxruntime-directml==1.21.0
```

**Para CPU apenas (após instalação base):**
```cmd
# Certifique-se de usar ONNX Runtime CPU
pip uninstall onnxruntime-gpu onnxruntime-directml -y
pip install onnxruntime
```

### 🐧 Instalação no Linux

#### Opção 1: Instalador Automático (Recomendado)

1. **Navegue até a pasta do projeto:**
   ```bash
   cd Deep-live
   ```

2. **Dê permissão de execução aos scripts:**
   ```bash
   chmod +x instalador/linux/*.sh
   ```

3. **Escolha e execute o instalador apropriado:**

   **Para GPU NVIDIA:**
   ```bash
   ./instalador/linux/gpu_nvidia.sh
   ```

   **Para GPU AMD:**
   ```bash
   ./instalador/linux/gpu_amd.sh
   ```

   **Para CPU apenas:**
   ```bash
   ./instalador/linux/somente_cpu.sh
   ```

4. **Aguarde a instalação completa** - O script irá:
   - Verificar se Python está instalado
   - Criar ambiente virtual automaticamente
   - Instalar todas as dependências
   - Baixar os modelos necessários

#### Opção 2: Instalação Manual

**Criando Ambiente Virtual no Linux:**

```bash
# Navegue até a pasta do projeto
cd Deep-live

# Crie o ambiente virtual
python3 -m venv venv

# Ative o ambiente virtual
source venv/bin/activate

# Atualize o pip
pip install --upgrade pip

# Instale as dependências
pip install -r requirements.txt
```

**Para GPU NVIDIA (após instalação base):**
```bash
# Certifique-se de ter CUDA Toolkit 12.8.0 e cuDNN instalados
# Instale PyTorch com CUDA
pip install -U torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# Instale ONNX Runtime GPU
pip uninstall onnxruntime onnxruntime-gpu -y
pip install onnxruntime-gpu==1.21.0
```

**Para GPU AMD (após instalação base):**
```bash
# Nota: DirectML é específico do Windows
# Em Linux, o script instalará para CPU automaticamente
# Para ROCm, consulte a documentação específica
pip uninstall onnxruntime-directml -y
pip install onnxruntime
```

**Para CPU apenas (após instalação base):**
```bash
# Certifique-se de usar ONNX Runtime CPU
pip uninstall onnxruntime-gpu onnxruntime-directml -y
pip install onnxruntime
```

---

## 🎮 Como Usar

### 🚀 Executando o Programa

Após a instalação, você pode executar o DEEP FACE de diferentes formas:

#### Para GPU NVIDIA:
```bash
# Windows
python run.py --execution-provider cuda

# Linux
python3 run.py --execution-provider cuda
```

#### Para GPU AMD (Windows):
```bash
python run.py --execution-provider directml
```

#### Para CPU (qualquer sistema):
```bash
# Windows
python run.py

# Linux
python3 run.py
```

O sistema detecta automaticamente o melhor provider disponível se você não especificar.

### 📸 Modo Imagem/Vídeo

1. Execute o programa
2. Selecione uma imagem de rosto de origem (source)
3. Selecione uma imagem ou vídeo de destino (target)
4. Clique em "Start"
5. O resultado será salvo na pasta de saída

### 🎥 Modo Webcam (Tempo Real)

1. Execute o programa
2. Selecione uma imagem de rosto de origem
3. Clique em "Live"
4. Aguarde a pré-visualização aparecer (10-30 segundos)
5. Use uma ferramenta de captura de tela como OBS para transmitir
6. Para trocar o rosto, selecione uma nova imagem de origem

---

## ⚙️ Requisitos de Sistema

### 💻 Mínimos (CPU apenas)

- **Processador**: Qualquer processador moderno (Intel/AMD)
- **RAM**: 8GB (recomendado 16GB)
- **Python**: 3.11 ou superior
- **Espaço em disco**: 5GB livres

### 🚀 Recomendados (com GPU)

#### NVIDIA:
- **GPU**: NVIDIA com suporte CUDA (Compute Capability 3.5+)
- **CUDA Toolkit**: 12.8.0
- **cuDNN**: v8.9.7 para CUDA 12.x
- **RAM**: 16GB ou mais
- **VRAM**: 4GB ou mais

#### AMD (Windows):
- **GPU**: AMD com suporte DirectML
- **Sistema**: Windows 10/11
- **RAM**: 16GB ou mais
- **VRAM**: 4GB ou mais

---

## 📁 Estrutura de Pastas

```
Deep-live/
├── instalador/          # Instaladores automáticos
│   ├── windows/         # Instaladores para Windows (.bat)
│   └── linux/           # Instaladores para Linux (.sh)
├── models/              # Modelos de IA (baixados automaticamente)
├── modules/             # Módulos do programa
├── run.py               # Arquivo principal para executar
├── requirements.txt     # Dependências Python
└── README.md           # Este arquivo
```

---

## 🔍 Solução de Problemas

### ❌ Python não encontrado

**Windows:**
- Certifique-se de que Python está instalado e adicionado ao PATH
- Durante a instalação do Python, marque "Add Python to PATH"

**Linux:**
- Instale Python: `sudo apt install python3 python3-pip` (Ubuntu/Debian)
- Ou: `sudo yum install python3 python3-pip` (CentOS/RHEL)

### ⚠️ Erro ao criar ambiente virtual

**Windows:**
```cmd
python -m pip install --upgrade pip
python -m venv venv
```

**Linux:**
```bash
python3 -m pip install --upgrade pip
python3 -m venv venv
```

### 🐛 Erro ao instalar dependências

Tente atualizar o pip primeiro:
```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### 🎮 GPU não detectada

**NVIDIA:**
- Verifique se CUDA Toolkit está instalado: `nvcc --version`
- Verifique se cuDNN está no PATH
- Certifique-se de que os drivers da GPU estão atualizados

**AMD (Windows):**
- DirectML funciona nativamente no Windows 10/11
- Certifique-se de que os drivers da GPU estão atualizados
- Não requer instalação adicional

### 📦 Modelos não baixados

Os modelos são baixados automaticamente durante a instalação. Se falhar:

1. Verifique sua conexão com a internet
2. Baixe manualmente de:
   - [inswapper_128_fp16.onnx](https://huggingface.co/hacksider/deep-live-cam/resolve/main/inswapper_128_fp16.onnx)
   - [inswapper_128.onnx](https://huggingface.co/hacksider/deep-live-cam/resolve/main/inswapper_128.onnx)
   - [GFPGANv1.4.pth](https://github.com/TencentARC/GFPGAN/releases/download/v1.3.4/GFPGANv1.4.pth)
3. Coloque os arquivos na pasta `models/`

---

## 📝 Notas Importantes

### ⚖️ Uso Ético

Este software é uma ferramenta poderosa. Use-o de forma responsável:

- ✅ Obtenha consentimento antes de usar o rosto de alguém
- ✅ Identifique claramente conteúdo gerado por IA
- ✅ Respeite direitos de imagem e privacidade
- ❌ Não use para criar conteúdo enganoso ou malicioso
- ❌ Não use para difamação ou assédio

### 🔒 Privacidade

- Todo o processamento é feito localmente em seu computador
- Nenhum dado é enviado para servidores externos
- Suas imagens e vídeos permanecem privados

### ⚡ Performance

- **Com GPU**: Processamento muito mais rápido (recomendado)
- **Sem GPU (CPU)**: Funciona perfeitamente, mas mais lento
  - Imagens: alguns segundos
  - Vídeos curtos: alguns minutos
  - Vídeos longos: pode demorar bastante (mas funciona!)

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para:

- Reportar bugs
- Sugerir melhorias
- Enviar pull requests
- Melhorar a documentação

---

## 📄 Licença

Este projeto é open-source. Consulte o arquivo LICENSE para mais detalhes.

---

<div align="center">

**DEEP FACE by Satoru Gojo** 🎭

*"Com grande poder vem grande responsabilidade"*

</div>
