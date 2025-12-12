import os
import sys
# single thread doubles cuda performance - needs to be set before torch import
if any(arg.startswith('--execution-provider') for arg in sys.argv):
    os.environ['OMP_NUM_THREADS'] = '1'
# reduce tensorflow log level
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import warnings
from typing import List
import platform
import signal
import shutil
import argparse
import torch
import onnxruntime
import tensorflow

import modules.globals
import modules.metadata
import modules.ui as ui
from modules.processors.frame.core import get_frame_processors_modules
from modules.utilities import has_image_extension, is_image, is_video, detect_fps, create_video, extract_frames, get_temp_frame_paths, restore_audio, create_temp, move_temp, clean_temp, normalize_output_path

if 'ROCMExecutionProvider' in modules.globals.execution_providers:
    del torch

warnings.filterwarnings('ignore', category=FutureWarning, module='insightface')
warnings.filterwarnings('ignore', category=UserWarning, module='torchvision')


def parse_args() -> None:
    signal.signal(signal.SIGINT, lambda signal_number, frame: destroy())
    program = argparse.ArgumentParser()
    program.add_argument('-s', '--source', help='select an source image', dest='source_path')
    program.add_argument('-t', '--target', help='select an target image or video', dest='target_path')
    program.add_argument('-o', '--output', help='select output file or directory', dest='output_path')
    program.add_argument('--frame-processor', help='pipeline of frame processors', dest='frame_processor', default=['face_swapper'], choices=['face_swapper', 'face_enhancer'], nargs='+')
    program.add_argument('--keep-fps', help='keep original fps', dest='keep_fps', action='store_true', default=False)
    program.add_argument('--keep-audio', help='keep original audio', dest='keep_audio', action='store_true', default=True)
    program.add_argument('--keep-frames', help='keep temporary frames', dest='keep_frames', action='store_true', default=False)
    program.add_argument('--many-faces', help='process every face', dest='many_faces', action='store_true', default=False)
    program.add_argument('--nsfw-filter', help='filter the NSFW image or video', dest='nsfw_filter', action='store_true', default=False)
    program.add_argument('--map-faces', help='map source target faces', dest='map_faces', action='store_true', default=False)
    program.add_argument('--mouth-mask', help='mask the mouth region', dest='mouth_mask', action='store_true', default=False)
    program.add_argument('--video-encoder', help='adjust output video encoder', dest='video_encoder', default='libx264', choices=['libx264', 'libx265', 'libvpx-vp9'])
    program.add_argument('--video-quality', help='adjust output video quality', dest='video_quality', type=int, default=18, choices=range(52), metavar='[0-51]')
    program.add_argument('-l', '--lang', help='Ui language', default="pt-br")
    program.add_argument('--live-mirror', help='The live camera display as you see it in the front-facing camera frame', dest='live_mirror', action='store_true', default=False)
    program.add_argument('--live-resizable', help='The live camera frame is resizable', dest='live_resizable', action='store_true', default=False)
    program.add_argument('--max-memory', help='maximum amount of RAM in GB', dest='max_memory', type=int, default=suggest_max_memory())
    program.add_argument('--execution-provider', help='execution provider', dest='execution_provider', default=['cpu'], choices=suggest_execution_providers(), nargs='+')
    program.add_argument('--execution-threads', help='number of execution threads', dest='execution_threads', type=int, default=suggest_execution_threads())
    program.add_argument('-v', '--version', action='version', version=f'{modules.metadata.name} {modules.metadata.version}')

    # register deprecated args
    program.add_argument('-f', '--face', help=argparse.SUPPRESS, dest='source_path_deprecated')
    program.add_argument('--cpu-cores', help=argparse.SUPPRESS, dest='cpu_cores_deprecated', type=int)
    program.add_argument('--gpu-vendor', help=argparse.SUPPRESS, dest='gpu_vendor_deprecated')
    program.add_argument('--gpu-threads', help=argparse.SUPPRESS, dest='gpu_threads_deprecated', type=int)

    args = program.parse_args()

    modules.globals.source_path = args.source_path
    modules.globals.target_path = args.target_path
    modules.globals.output_path = normalize_output_path(modules.globals.source_path, modules.globals.target_path, args.output_path)
    modules.globals.frame_processors = args.frame_processor
    modules.globals.headless = args.source_path or args.target_path or args.output_path
    modules.globals.keep_fps = args.keep_fps
    modules.globals.keep_audio = args.keep_audio
    modules.globals.keep_frames = args.keep_frames
    modules.globals.many_faces = args.many_faces
    modules.globals.mouth_mask = args.mouth_mask
    modules.globals.nsfw_filter = args.nsfw_filter
    modules.globals.map_faces = args.map_faces
    modules.globals.video_encoder = args.video_encoder
    modules.globals.video_quality = args.video_quality
    modules.globals.live_mirror = args.live_mirror
    modules.globals.live_resizable = args.live_resizable
    modules.globals.max_memory = args.max_memory
    modules.globals.execution_providers = decode_execution_providers(args.execution_provider)
    modules.globals.execution_threads = args.execution_threads
    modules.globals.lang = args.lang

    #for ENHANCER tumbler:
    if 'face_enhancer' in args.frame_processor:
        modules.globals.fp_ui['face_enhancer'] = True
    else:
        modules.globals.fp_ui['face_enhancer'] = False

    # translate deprecated args
    if args.source_path_deprecated:
        print('\033[33mArgument -f and --face are deprecated. Use -s and --source instead.\033[0m')
        modules.globals.source_path = args.source_path_deprecated
        modules.globals.output_path = normalize_output_path(args.source_path_deprecated, modules.globals.target_path, args.output_path)
    if args.cpu_cores_deprecated:
        print('\033[33mArgument --cpu-cores is deprecated. Use --execution-threads instead.\033[0m')
        modules.globals.execution_threads = args.cpu_cores_deprecated
    if args.gpu_vendor_deprecated == 'apple':
        print('\033[33mArgument --gpu-vendor apple is deprecated. Use --execution-provider coreml instead.\033[0m')
        modules.globals.execution_providers = decode_execution_providers(['coreml'])
    if args.gpu_vendor_deprecated == 'nvidia':
        print('\033[33mArgument --gpu-vendor nvidia is deprecated. Use --execution-provider cuda instead.\033[0m')
        modules.globals.execution_providers = decode_execution_providers(['cuda'])
    if args.gpu_vendor_deprecated == 'amd':
        print('\033[33mArgument --gpu-vendor amd is deprecated. Use --execution-provider cuda instead.\033[0m')
        modules.globals.execution_providers = decode_execution_providers(['rocm'])
    if args.gpu_threads_deprecated:
        print('\033[33mArgument --gpu-threads is deprecated. Use --execution-threads instead.\033[0m')
        modules.globals.execution_threads = args.gpu_threads_deprecated


def encode_execution_providers(execution_providers: List[str]) -> List[str]:
    return [execution_provider.replace('ExecutionProvider', '').lower() for execution_provider in execution_providers]


def decode_execution_providers(execution_providers: List[str]) -> List[str]:
    return [provider for provider, encoded_execution_provider in zip(onnxruntime.get_available_providers(), encode_execution_providers(onnxruntime.get_available_providers()))
            if any(execution_provider in encoded_execution_provider for execution_provider in execution_providers)]


def suggest_max_memory() -> int:
    if platform.system().lower() == 'darwin':
        return 4
    return 16


def suggest_execution_providers() -> List[str]:
    return encode_execution_providers(onnxruntime.get_available_providers())


def suggest_execution_threads() -> int:
    if 'DmlExecutionProvider' in modules.globals.execution_providers:
        return 1
    if 'ROCMExecutionProvider' in modules.globals.execution_providers:
        return 1
    return 8


def limit_resources() -> None:
    # prevent tensorflow memory leak
    gpus = tensorflow.config.experimental.list_physical_devices('GPU')
    for gpu in gpus:
        tensorflow.config.experimental.set_memory_growth(gpu, True)
    # limit memory usage
    if modules.globals.max_memory:
        memory = modules.globals.max_memory * 1024 ** 3
        if platform.system().lower() == 'darwin':
            memory = modules.globals.max_memory * 1024 ** 6
        if platform.system().lower() == 'windows':
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetProcessWorkingSetSize(-1, ctypes.c_size_t(memory), ctypes.c_size_t(memory))
        else:
            import resource
            resource.setrlimit(resource.RLIMIT_DATA, (memory, memory))


def release_resources() -> None:
    if 'CUDAExecutionProvider' in modules.globals.execution_providers:
        torch.cuda.empty_cache()


def pre_check() -> bool:
    if sys.version_info < (3, 9):
        update_status('Python version is not supported - please upgrade to 3.9 or higher.')
        return False
    if not shutil.which('ffmpeg'):
        update_status('ffmpeg is not installed.')
        return False
    return True


def update_status(message: str, scope: str = 'DLC.CORE') -> None:
    print(f'[{scope}] {message}')
    if not modules.globals.headless:
        ui.update_status(message)


def generate_unique_output_path(target_path: str, output_dir: str, file_id: int) -> str:
    """Generate a unique output path with ID to avoid overwriting."""
    target_name, target_extension = os.path.splitext(os.path.basename(target_path))
    
    # Create unique filename with ID using uptopt-idaqui parameter
    unique_name = f"uptopt-{file_id:04d}{target_extension}"
    return os.path.join(output_dir, unique_name)


def process_single_file(target_path: str, output_path: str) -> bool:
    """Process a single file (image or video). Returns True if successful."""
    # Verificar se processamento VPS está habilitado
    if modules.globals.vps_enabled and modules.globals.vps_server_url:
        try:
            from modules.vps.client_ws import process_remote_file
            update_status('Processando remotamente na VPS...')
            return process_remote_file(
                modules.globals.source_path,
                target_path,
                output_path,
                modules.globals.vps_server_url
            )
        except Exception as e:
            update_status(f'Erro no processamento VPS: {str(e)}')
            update_status('Tentando processamento local...')
            # Continuar com processamento local em caso de erro
    
    try:
        # process image to image
        if has_image_extension(target_path):
            if modules.globals.nsfw_filter and ui.check_and_ignore_nsfw(target_path, None):
                return False
            try:
                shutil.copy2(target_path, output_path)
            except Exception as e:
                print("Error copying file:", str(e))
                return False
            # Process each frame processor in sequence
            # Each processor reads from output_path (result of previous processor) and writes back to output_path
            # This ensures: face_swapper processes original -> face_enhancer processes swapped result
            current_input = output_path  # Start with copied original image
            for frame_processor in get_frame_processors_modules(modules.globals.frame_processors):
                update_status('Progressing...', frame_processor.NAME)
                # Each processor reads from current_input and writes to output_path
                frame_processor.process_image(modules.globals.source_path, current_input, output_path)
                # Next processor will read from the updated output_path
                current_input = output_path
                release_resources()
            if is_image(target_path):
                update_status('Processing to image succeed!')
            else:
                update_status('Processing to image failed!')
            return True
        
        # process image to videos
        if modules.globals.nsfw_filter and ui.check_and_ignore_nsfw(target_path, None):
            return False

        # In folder mode, always extract frames (use simple mode)
        # Otherwise, extract frames only if not using map_faces
        should_extract = modules.globals.process_folder or not modules.globals.map_faces
        
        if should_extract:
            update_status('Creating temp resources...')
            create_temp(target_path)
            update_status('Extracting frames...')
            extract_frames(target_path)

        temp_frame_paths = get_temp_frame_paths(target_path)
        for frame_processor in get_frame_processors_modules(modules.globals.frame_processors):
            update_status('Progressing...', frame_processor.NAME)
            frame_processor.process_video(modules.globals.source_path, temp_frame_paths)
            release_resources()
        # handles fps
        if modules.globals.keep_fps:
            update_status('Detecting fps...')
            fps = detect_fps(target_path)
            update_status(f'Creating video with {fps} fps...')
            create_video(target_path, fps)
        else:
            update_status('Creating video with 30.0 fps...')
            create_video(target_path)
        # handle audio
        if modules.globals.keep_audio:
            if modules.globals.keep_fps:
                update_status('Restoring audio...')
            else:
                update_status('Restoring audio might cause issues as fps are not kept...')
            restore_audio(target_path, output_path)
        else:
            move_temp(target_path, output_path)
        # clean and validate
        clean_temp(target_path)
        if is_video(target_path):
            update_status('Processing to video succeed!')
        else:
            update_status('Processing to video failed!')
        return True
    except Exception as e:
        update_status(f'Error processing file: {str(e)}')
        return False


def start() -> None:
    for frame_processor in get_frame_processors_modules(modules.globals.frame_processors):
        if not frame_processor.pre_start():
            return
    
    # Check if processing folder mode
    if modules.globals.process_folder and modules.globals.file_queue:
        # Process all files in queue
        if not modules.globals.source_path:
            update_status('Please select a source image first')
            return
        
        # Select output directory
        if not modules.globals.headless:
            output_dir = ui.select_output_directory()
            if not output_dir:
                update_status('Output directory not selected')
                return
        else:
            # In headless mode, use folder_path as output directory
            output_dir = modules.globals.folder_path
            if not output_dir:
                update_status('Output directory not specified')
                return
        
        total_files = len(modules.globals.file_queue)
        update_status(f'Processing {total_files} files in queue...')
        
        successful = 0
        failed = 0
        
        for file_id, target_path in enumerate(modules.globals.file_queue, 1):
            update_status(f'Processing file {file_id}/{total_files}: {os.path.basename(target_path)}')
            
            # Generate unique output path
            output_path = generate_unique_output_path(target_path, output_dir, file_id)
            
            # Process the file
            if process_single_file(target_path, output_path):
                successful += 1
            else:
                failed += 1
        
        update_status(f'Queue processing complete! Success: {successful}, Failed: {failed}')
        modules.globals.file_queue = []  # Clear queue after processing
        return
    
    # Normal single file processing
    if not modules.globals.target_path:
        update_status('Please select a target file')
        return
    
    update_status('Processing...')
    if process_single_file(modules.globals.target_path, modules.globals.output_path):
        update_status('Processing complete!')
    else:
        update_status('Processing failed!')


def destroy(to_quit=True) -> None:
    if modules.globals.target_path:
        clean_temp(modules.globals.target_path)
    if to_quit: quit()


def run() -> None:
    parse_args()
    if not pre_check():
        return
    for frame_processor in get_frame_processors_modules(modules.globals.frame_processors):
        if not frame_processor.pre_check():
            return
    limit_resources()
    if modules.globals.headless:
        start()
    else:
        window = ui.init(start, destroy, modules.globals.lang)
        window.mainloop()
