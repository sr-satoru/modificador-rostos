# Como Testar o Servidor VPS

## 1. Iniciar o Servidor na VPS

Na VPS com GPU, execute:

```bash
cd /caminho/para/Deep-live/modules/vps
python server_ws.py
```

O servidor vai:
- Detectar GPU automaticamente (CUDA/TensorRT/CPU)
- Escutar na porta 8765
- Mostrar: "Servidor rodando. Aguardando conexões..."

## 2. Testar Conexão do PC Local

No PC local:

1. Abra a interface do Deep Live Cam
2. Vá na aba **"Configurações"**
3. Digite o IP da VPS: `IP_DA_VPS:8765`
   - Exemplo: `192.168.1.100:8765`
   - Ou IP público: `45.67.89.123:8765`
4. Clique em **"Salvar IP"**
5. Clique em **"Testar Conexão"**

### Resultados do Teste:

**✅ Sucesso:**
- "Conexão OK! GPU: CUDAExecutionProvider"
- Ou: "Conexão OK! GPU: CPUExecutionProvider" (se não tiver GPU)

**❌ Erro:**
- "Conexão recusada" → Servidor não está rodando
- "IP não encontrado" → IP incorreto
- "Timeout" → Firewall bloqueando ou servidor lento

## 3. Como Funciona o Processamento

### Fluxo Completo:

```
1. PC Local (você)
   ↓
   Seleciona source + target
   Marca checkbox "GPU Externa (VPS)"
   Clica "Start"
   ↓
2. Cliente WebSocket
   ↓
   Conecta ao servidor VPS (ws://IP:8765)
   Envia arquivos codificados em base64
   Envia configurações (keep_fps, keep_audio, etc)
   ↓
3. Servidor VPS
   ↓
   Recebe arquivos
   Decodifica base64 → arquivos temporários
   Processa com GPU (face swap)
   Codifica resultado em base64
   ↓
4. Cliente WebSocket
   ↓
   Recebe resultado processado
   Decodifica base64 → salva arquivo
   ↓
5. PC Local
   ↓
   Arquivo processado salvo!
```

### Comandos WebSocket:

**PING** (teste de conexão):
```json
{"comando": "PING"}
→ Resposta: {"comando": "PONG"}
```

**INFO** (informações do servidor):
```json
{"comando": "INFO"}
→ Resposta: {"comando": "INFO", "providers": ["CUDAExecutionProvider"], "status": "online"}
```

**PROCESS** (processar arquivo):
```json
{
  "comando": "PROCESS",
  "source_file": "base64...",
  "target_file": "base64...",
  "config": {...}
}
→ Respostas: {"comando": "PROCESSANDO", "progresso": 50, ...}
→ Final: {"comando": "COMPLETO", "arquivo": "base64..."}
```

## 4. Troubleshooting

### Servidor não conecta:
- Verifique se o servidor está rodando na VPS
- Verifique se a porta 8765 está aberta no firewall
- Teste com: `telnet IP_DA_VPS 8765`

### Processamento falha:
- Verifique logs do servidor na VPS
- Verifique se os modelos estão instalados
- Verifique espaço em disco na VPS

### Conexão lenta:
- Arquivos grandes demoram mais para upload/download
- Use conexão estável
- Considere comprimir arquivos antes

## 5. Exemplo de Uso

1. **Na VPS:**
   ```bash
   python modules/vps/server_ws.py
   ```

2. **No PC:**
   - Abra Deep Live Cam
   - Aba "Configurações"
   - Digite IP: `192.168.1.100:8765`
   - Clique "Salvar IP"
   - Clique "Testar Conexão" → Deve mostrar "Conexão OK!"
   - Marque "Habilitar GPU Externa (VPS)"
   - Volte para aba "Processamento"
   - Selecione source e target
   - Clique "Start"
   - Aguarde processamento remoto!

