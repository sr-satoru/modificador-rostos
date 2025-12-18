# Instalação do Servidor VPS

## O que precisa na VPS:

### 1. Sistema Operacional
- Ubuntu 20.04+ ou similar (Linux)
- Acesso root ou sudo

### 2. GPU NVIDIA (se tiver)
- Drivers NVIDIA instalados
- CUDA Toolkit 11.8+ ou 12.x
- Verificar: `nvidia-smi`

### 3. Dependências do Sistema

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python 3.10+
sudo apt install python3 python3-pip python3-venv -y

# Instalar ffmpeg (obrigatório)
sudo apt install ffmpeg -y

# Instalar outras dependências
sudo apt install git wget curl -y
```

### 4. Copiar Código para VPS

**Opção A - Via Git:**
```bash
git clone <seu-repositorio>
cd Deep-live
```

**Opção B - Via SCP (do seu PC):**
```bash
# No seu PC local:
scp -r /caminho/para/Deep-live usuario@IP_DA_VPS:/home/usuario/
```

**Opção C - Via USB/Transferência:**
- Compacte a pasta `modules/vps` e `modules/` (dependências)
- Transfira para VPS
- Descompacte

### 5. Estrutura de Pastas na VPS

Na VPS, você precisa ter:

```
/home/usuario/Deep-live/
├── modules/
│   ├── vps/
│   │   ├── server_ws.py      ← Servidor principal
│   │   └── __init__.py
│   ├── processors/
│   │   └── frame/
│   │       ├── face_swapper.py
│   │       └── ...
│   ├── face_analyser.py
│   ├── utilities.py
│   ├── globals.py
│   └── core.py
├── models/
│   ├── inswapper_128_fp16.onnx
│   └── GFPGANv1.4.pth
└── requirements.txt
```

### 6. Instalar Dependências Python

```bash
cd /home/usuario/Deep-live

# Criar ambiente virtual
python3 -m venv venv

# Ativar ambiente virtual
source venv/bin/activate

# Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt

# Instalar websockets especificamente
pip install websockets>=12.0
```

### 7. Baixar Modelos (se não tiver)

```bash
cd models/

# Baixar inswapper
wget https://huggingface.co/hacksider/deep-live-cam/resolve/main/inswapper_128_fp16.onnx

# Baixar GFPGAN
wget https://huggingface.co/hacksider/deep-live-cam/resolve/main/GFPGANv1.4.pth
```

### 8. Configurar Firewall

```bash
# Abrir porta 8765
sudo ufw allow 8765/tcp
sudo ufw reload

# Verificar
sudo ufw status
```

### 9. Testar Servidor

```bash
cd /home/usuario/Deep-live/modules/vps
python server_ws.py
```

Deve aparecer:
```
============================================================
Servidor VPS - Processamento Remoto com GPU
============================================================
Providers: ['CUDAExecutionProvider']
Porta: 8765
Temp dir: temp_vps
============================================================
Servidor rodando. Aguardando conexões...
```

### 10. Rodar em Background (Opcional)

**Com screen:**
```bash
sudo apt install screen -y
screen -S vps_server
cd /home/usuario/Deep-live/modules/vps
python server_ws.py
# Pressione Ctrl+A depois D para sair (servidor continua rodando)
```

**Com systemd (serviço):**
```bash
# Criar arquivo de serviço
sudo nano /etc/systemd/system/deep-live-vps.service
```

Conteúdo do arquivo:
```ini
[Unit]
Description=Deep Live Cam VPS Server
After=network.target

[Service]
Type=simple
User=usuario
WorkingDirectory=/home/usuario/Deep-live/modules/vps
Environment="PATH=/home/usuario/Deep-live/venv/bin"
ExecStart=/home/usuario/Deep-live/venv/bin/python server_ws.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Ativar serviço:
```bash
sudo systemctl daemon-reload
sudo systemctl enable deep-live-vps
sudo systemctl start deep-live-vps
sudo systemctl status deep-live-vps
```

## Checklist Rápido:

- [ ] Python 3.10+ instalado
- [ ] ffmpeg instalado
- [ ] Código copiado para VPS
- [ ] Ambiente virtual criado e ativado
- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] Modelos baixados (inswapper, GFPGAN)
- [ ] Porta 8765 aberta no firewall
- [ ] Servidor testado e rodando
- [ ] IP da VPS anotado

## Verificar se está tudo OK:

```bash
# Verificar Python
python3 --version

# Verificar GPU (se tiver NVIDIA)
nvidia-smi

# Verificar ffmpeg
ffmpeg -version

# Verificar porta aberta
sudo netstat -tulpn | grep 8765

# Testar servidor
cd modules/vps
python server_ws.py
```

## Problemas Comuns:

**"No module named 'websockets'"**
→ `pip install websockets`

**"CUDA not found"**
→ Instale drivers NVIDIA e CUDA Toolkit

**"Port 8765 already in use"**
→ Outro processo usando a porta, mate-o ou mude a porta

**"Permission denied"**
→ Use `sudo` ou ajuste permissões

