"""
Cliente WebSocket para processamento remoto de arquivos.
Roda no PC local e se conecta à VPS com GPU.
"""
import os
import json
import base64
import asyncio
import websockets
from typing import Optional, Dict, Any, Tuple
import modules.globals
from modules.core import update_status


class VPSClient:
    """Cliente WebSocket para VPS."""
    
    def __init__(self, server_url: str):
        """
        Inicializa cliente.
        
        Args:
            server_url: URL do servidor (ex: '192.168.1.100:8765' ou 'ws://192.168.1.100:8765')
        """
        if not server_url.startswith('ws://') and not server_url.startswith('wss://'):
            server_url = f'ws://{server_url}'
        self.server_url = server_url
    
    def encode_file(self, file_path: str) -> str:
        """Codifica arquivo para base64."""
        with open(file_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    
    def decode_file(self, file_b64: str, output_path: str):
        """Decodifica base64 e salva arquivo."""
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        file_bytes = base64.b64decode(file_b64)
        with open(output_path, 'wb') as f:
            f.write(file_bytes)
    
    async def test_connection(self) -> Tuple[bool, str]:
        """
        Testa conexão com o servidor.
        
        Returns:
            Tuple (sucesso: bool, mensagem: str)
        """
        try:
            update_status("Testando conexão com servidor VPS...")
            
            async with websockets.connect(
                self.server_url, 
                ping_interval=30, 
                ping_timeout=5
            ) as websocket:
                # Enviar PING
                await websocket.send(json.dumps({'comando': 'PING'}))
                
                # Aguardar resposta com timeout
                try:
                    resposta = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(resposta)
                    
                    if data.get('comando') == 'PONG':
                        # Tentar obter informações do servidor
                        await websocket.send(json.dumps({'comando': 'INFO'}))
                        try:
                            info_resp = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                            info_data = json.loads(info_resp)
                            if info_data.get('comando') == 'INFO':
                                providers = info_data.get('providers', [])
                                return True, f"Conexão OK! GPU: {', '.join(providers) if providers else 'CPU'}"
                        except asyncio.TimeoutError:
                            return True, "Conexão OK! (sem info de GPU)"
                    
                    return True, "Conexão estabelecida com sucesso!"
                    
                except asyncio.TimeoutError:
                    return False, "Timeout: servidor não respondeu"
                
        except websockets.exceptions.InvalidURI:
            return False, "URL inválida. Use formato: IP:PORTA (ex: 192.168.1.100:8765)"
        except websockets.exceptions.ConnectionRefused:
            return False, "Conexão recusada. Verifique se o servidor está rodando."
        except OSError as e:
            if "Name or service not known" in str(e):
                return False, "IP não encontrado. Verifique o endereço do servidor."
            return False, f"Erro de conexão: {str(e)}"
        except Exception as e:
            return False, f"Erro: {str(e)}"
    
    def test_connection_sync(self) -> Tuple[bool, str]:
        """Versão síncrona do teste de conexão."""
        return asyncio.run(self.test_connection())
    
    async def process_remote(self, source_path: str, target_path: str, 
                            output_path: str) -> bool:
        """
        Processa arquivo remotamente.
        
        Args:
            source_path: Caminho do arquivo source local
            target_path: Caminho do arquivo target local
            output_path: Caminho para salvar resultado local
        
        Returns:
            True se bem-sucedido, False caso contrário
        """
        try:
            update_status("Conectando ao servidor VPS...")
            
            async with websockets.connect(self.server_url, ping_interval=30, ping_timeout=10) as websocket:
                update_status("Conectado! Enviando arquivos...")
                
                # Codificar arquivos
                source_b64 = self.encode_file(source_path)
                target_b64 = self.encode_file(target_path)
                
                # Preparar configuração
                config = {
                    'frame_processors': modules.globals.frame_processors,
                    'keep_fps': modules.globals.keep_fps,
                    'keep_audio': modules.globals.keep_audio,
                    'keep_frames': modules.globals.keep_frames,
                    'many_faces': modules.globals.many_faces,
                    'map_faces': modules.globals.map_faces,
                    'color_correction': modules.globals.color_correction,
                    'nsfw_filter': modules.globals.nsfw_filter,
                    'mouth_mask': modules.globals.mouth_mask,
                    'video_encoder': modules.globals.video_encoder,
                    'video_quality': modules.globals.video_quality,
                    'execution_providers': modules.globals.execution_providers,
                    'execution_threads': modules.globals.execution_threads,
                    'max_memory': modules.globals.max_memory,
                    'opacity': modules.globals.opacity,
                    'sharpness': modules.globals.sharpness,
                }
                
                # Enviar comando de processamento
                comando = {
                    'comando': 'PROCESS',
                    'source_file': source_b64,
                    'target_file': target_b64,
                    'config': config
                }
                
                await websocket.send(json.dumps(comando))
                
                # Aguardar resposta
                while True:
                    resposta = await websocket.recv()
                    data = json.loads(resposta)
                    
                    comando_resp = data.get('comando')
                    
                    if comando_resp == 'PROCESSANDO':
                        progresso = data.get('progresso', 0)
                        mensagem = data.get('mensagem', 'Processando...')
                        update_status(f"{mensagem} ({progresso}%)")
                    
                    elif comando_resp == 'COMPLETO':
                        # Receber arquivo processado
                        arquivo_b64 = data.get('arquivo')
                        if arquivo_b64:
                            update_status("Salvando resultado...")
                            self.decode_file(arquivo_b64, output_path)
                            update_status("Processamento concluído!")
                            return True
                        else:
                            update_status("Erro: arquivo não recebido")
                            return False
                    
                    elif comando_resp == 'ERRO':
                        erro = data.get('mensagem', 'Erro desconhecido')
                        update_status(f"Erro no servidor: {erro}")
                        return False
                
        except websockets.exceptions.ConnectionClosed:
            update_status("Conexão com servidor fechada")
            return False
        except Exception as e:
            update_status(f"Erro ao processar remotamente: {str(e)}")
            return False


def process_remote_file(source_path: str, target_path: str, output_path: str, 
                       server_url: str) -> bool:
    """
    Função helper síncrona para processar arquivo remotamente.
    
    Args:
        source_path: Caminho do arquivo source
        target_path: Caminho do arquivo target
        output_path: Caminho para salvar resultado
        server_url: URL do servidor VPS
    
    Returns:
        True se bem-sucedido, False caso contrário
    """
    client = VPSClient(server_url)
    return asyncio.run(client.process_remote(source_path, target_path, output_path))

