"""
Servidor WebSocket para processamento remoto de arquivos completos (vídeos/imagens).
Roda na VPS com GPU.
Inspirado no Deep-Live-Cam-Server, mas adaptado para processar arquivos completos.
"""
import os
import sys
import json
import shutil
import asyncio
import websockets
import base64
import tempfile
import cv2
from pathlib import Path
from typing import Dict, Any

# Adicionar path dos módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import modules
import modules.globals
import modules.core
from modules.utilities import is_image, is_video, has_image_extension
from modules.face_analyser import get_one_face
from modules.processors.frame.core import get_frame_processors_modules
from modules.utilities import (
    create_temp, extract_frames, get_temp_frame_paths,
    detect_fps, create_video, restore_audio, move_temp, clean_temp
)
import onnxruntime


def configurar_providers():
    """Configura os execution providers disponíveis (GPU/CPU)."""
    providers = onnxruntime.get_available_providers()
    print(f"Providers disponíveis: {providers}")
    
    if 'TensorrtExecutionProvider' in providers:
        return ['TensorrtExecutionProvider']
    if 'CUDAExecutionProvider' in providers:
        print("Usando CUDA para processamento")
        return ['CUDAExecutionProvider']
    
    print("Usando CPU para processamento")
    return ['CPUExecutionProvider']


# Configurar providers na inicialização
modules.globals.execution_providers = configurar_providers()
print(f"Providers configurados: {modules.globals.execution_providers}")

# Pasta temporária para arquivos
TEMP_DIR = Path("temp_vps")
TEMP_DIR.mkdir(exist_ok=True)


class FileProcessingServer:
    """Servidor WebSocket para processar arquivos completos."""
    
    def __init__(self):
        self.clientes_ativos = set()
        self.jobs_ativos = {}  # job_id -> info do job
        
    def decode_file(self, file_b64: str, file_type: str) -> str:
        """Decodifica arquivo base64 e salva temporariamente."""
        import uuid
        file_bytes = base64.b64decode(file_b64)
        # Detectar extensão pelo conteúdo ou usar padrão
        ext = '.jpg' if file_type == 'source' else '.mp4'
        temp_path = TEMP_DIR / f"{file_type}_{uuid.uuid4().hex[:8]}{ext}"
        temp_path.write_bytes(file_bytes)
        return str(temp_path)
    
    def encode_file(self, file_path: str) -> str:
        """Codifica arquivo para base64."""
        file_bytes = Path(file_path).read_bytes()
        return base64.b64encode(file_bytes).decode('utf-8')
    
    async def processar_arquivo(self, source_path: str, target_path: str, 
                                config: Dict[str, Any], job_id: str) -> str:
        """Processa um arquivo completo (imagem ou vídeo)."""
        try:
            # Aplicar configurações
            self.apply_config(config)
            
            # Determinar tipo
            is_target_image = is_image(target_path)
            
            # Gerar output path
            output_path = TEMP_DIR / f"output_{job_id}"
            if is_target_image:
                output_path = output_path.with_suffix('.png')
            else:
                output_path = output_path.with_suffix('.mp4')
            
            # Processar
            if is_target_image:
                # Processar imagem
                shutil.copy2(target_path, str(output_path))
                
                source_face = get_one_face(cv2.imread(source_path))
                if not source_face:
                    raise Exception("Nenhum rosto encontrado na imagem source")
                
                for frame_processor in get_frame_processors_modules(modules.globals.frame_processors):
                    frame_processor.process_image(source_path, str(output_path), str(output_path))
                    modules.core.release_resources()
            else:
                # Processar vídeo
                if not modules.globals.map_faces:
                    create_temp(target_path)
                    extract_frames(target_path)
                
                temp_frame_paths = get_temp_frame_paths(target_path)
                
                for frame_processor in get_frame_processors_modules(modules.globals.frame_processors):
                    frame_processor.process_video(source_path, temp_frame_paths)
                    modules.core.release_resources()
                
                # Criar vídeo
                if modules.globals.keep_fps:
                    fps = detect_fps(target_path)
                    create_video(target_path, fps)
                else:
                    create_video(target_path)
                
                # Áudio
                if modules.globals.keep_audio:
                    restore_audio(target_path, str(output_path))
                else:
                    move_temp(target_path, str(output_path))
                
                clean_temp(target_path)
            
            return str(output_path)
            
        except Exception as e:
            raise Exception(f"Erro ao processar: {str(e)}")
    
    def apply_config(self, config: Dict[str, Any]):
        """Aplica configurações recebidas do cliente."""
        modules.globals.frame_processors = config.get('frame_processors', ['face_swapper'])
        modules.globals.keep_fps = config.get('keep_fps', True)
        modules.globals.keep_audio = config.get('keep_audio', True)
        modules.globals.keep_frames = config.get('keep_frames', False)
        modules.globals.many_faces = config.get('many_faces', False)
        modules.globals.map_faces = config.get('map_faces', False)
        modules.globals.color_correction = config.get('color_correction', False)
        modules.globals.nsfw_filter = config.get('nsfw_filter', False)
        modules.globals.mouth_mask = config.get('mouth_mask', False)
        modules.globals.video_encoder = config.get('video_encoder', 'libx264')
        modules.globals.video_quality = config.get('video_quality', 18)
        modules.globals.execution_threads = config.get('execution_threads', 8)
        modules.globals.max_memory = config.get('max_memory', 16)
        modules.globals.opacity = config.get('opacity', 1.0)
        modules.globals.sharpness = config.get('sharpness', 0.0)
        
        if config.get('execution_providers'):
            modules.globals.execution_providers = config['execution_providers']
    
    async def processar_cliente(self, websocket, path):
        """Processa conexão de cliente."""
        self.clientes_ativos.add(websocket)
        print(f"Cliente conectado. Total: {len(self.clientes_ativos)}")
        
        try:
            async for mensagem in websocket:
                try:
                    data = json.loads(mensagem)
                    comando = data.get('comando')
                    
                    if comando == 'PROCESS':
                        # Processar arquivo completo
                        await self.handle_process(websocket, data)
                    elif comando == 'PING':
                        # Heartbeat
                        await websocket.send(json.dumps({'comando': 'PONG'}))
                    elif comando == 'INFO':
                        # Informações do servidor
                        await websocket.send(json.dumps({
                            'comando': 'INFO',
                            'providers': modules.globals.execution_providers,
                            'status': 'online'
                        }))
                    else:
                        await websocket.send(json.dumps({
                            'comando': 'ERRO',
                            'mensagem': f'Comando desconhecido: {comando}'
                        }))
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        'comando': 'ERRO',
                        'mensagem': 'JSON inválido'
                    }))
                except Exception as e:
                    await websocket.send(json.dumps({
                        'comando': 'ERRO',
                        'mensagem': str(e)
                    }))
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clientes_ativos.discard(websocket)
            print(f"Cliente desconectado. Restantes: {len(self.clientes_ativos)}")
    
    async def handle_process(self, websocket, data: Dict[str, Any]):
        """Processa um job completo."""
        import uuid
        job_id = str(uuid.uuid4())
        
        try:
            # Decodificar arquivos
            source_b64 = data.get('source_file')
            target_b64 = data.get('target_file')
            config = data.get('config', {})
            
            if not source_b64 or not target_b64:
                await websocket.send(json.dumps({
                    'comando': 'ERRO',
                    'mensagem': 'Arquivos source e target são obrigatórios'
                }))
                return
            
            # Notificar início
            await websocket.send(json.dumps({
                'comando': 'PROCESSANDO',
                'job_id': job_id,
                'progresso': 10,
                'mensagem': 'Decodificando arquivos...'
            }))
            
            # Decodificar e salvar arquivos
            source_path = self.decode_file(source_b64, 'source')
            target_path = self.decode_file(target_b64, 'target')
            
            await websocket.send(json.dumps({
                'comando': 'PROCESSANDO',
                'job_id': job_id,
                'progresso': 30,
                'mensagem': 'Processando arquivo...'
            }))
            
            # Processar
            output_path = await self.processar_arquivo(source_path, target_path, config, job_id)
            
            await websocket.send(json.dumps({
                'comando': 'PROCESSANDO',
                'job_id': job_id,
                'progresso': 90,
                'mensagem': 'Codificando resultado...'
            }))
            
            # Codificar resultado
            output_b64 = self.encode_file(output_path)
            
            # Enviar resultado
            await websocket.send(json.dumps({
                'comando': 'COMPLETO',
                'job_id': job_id,
                'progresso': 100,
                'arquivo': output_b64,
                'mensagem': 'Processamento concluído!'
            }))
            
            # Limpar arquivos temporários
            try:
                os.remove(source_path)
                os.remove(target_path)
                os.remove(output_path)
            except:
                pass
                
        except Exception as e:
            await websocket.send(json.dumps({
                'comando': 'ERRO',
                'job_id': job_id,
                'mensagem': str(e)
            }))


async def main():
    """Inicia o servidor WebSocket."""
    server = FileProcessingServer()
    
    print("=" * 60)
    print("Servidor VPS - Processamento Remoto com GPU")
    print("=" * 60)
    print(f"Providers: {modules.globals.execution_providers}")
    print(f"Porta: 8765")
    print(f"Temp dir: {TEMP_DIR}")
    print("=" * 60)
    
    # Pre-check
    if not modules.core.pre_check():
        print("Pre-check falhou!")
        sys.exit(1)
    
    # Inicializar frame processors
    for frame_processor in get_frame_processors_modules(modules.globals.frame_processors):
        if not frame_processor.pre_start():
            print(f"Falha ao inicializar {frame_processor.NAME}")
            sys.exit(1)
    
    modules.core.limit_resources()
    
    # Iniciar servidor
    async with websockets.serve(
        server.processar_cliente,
        '0.0.0.0',
        8765,
        ping_interval=30,
        ping_timeout=10
    ):
        print("Servidor rodando. Aguardando conexões...")
        await asyncio.Future()  # Manter rodando


if __name__ == "__main__":
    import cv2
    asyncio.run(main())

