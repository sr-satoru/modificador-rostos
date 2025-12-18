import os
import webbrowser
import customtkinter as ctk
from typing import Callable, Tuple
import cv2
from cv2_enumerate_cameras import enumerate_cameras  # Add this import
from PIL import Image, ImageOps
import time
import json
import modules.globals
import modules.metadata
from modules.face_analyser import (
    get_one_face,
    get_unique_faces_from_target_image,
    get_unique_faces_from_target_video,
    add_blank_map,
    has_valid_map,
    simplify_maps,
)
from modules.capturer import get_video_frame, get_video_frame_total
from modules.processors.frame.core import get_frame_processors_modules
from modules.utilities import (
    is_image,
    is_video,
    resolve_relative_path,
    has_image_extension,
)
from modules.video_capture import VideoCapturer
from modules.gettext import LanguageManager
from modules import globals
import platform

if platform.system() == "Windows":
    from pygrabber.dshow_graph import FilterGraph

ROOT = None
POPUP = None
POPUP_LIVE = None
ROOT_HEIGHT = 750
ROOT_WIDTH = 600

PREVIEW = None
PREVIEW_MAX_HEIGHT = 700
PREVIEW_MAX_WIDTH = 1200
PREVIEW_DEFAULT_WIDTH = 960
PREVIEW_DEFAULT_HEIGHT = 540

POPUP_WIDTH = 750
POPUP_HEIGHT = 810
POPUP_SCROLL_WIDTH = (740,)
POPUP_SCROLL_HEIGHT = 700

POPUP_LIVE_WIDTH = 900
POPUP_LIVE_HEIGHT = 820
POPUP_LIVE_SCROLL_WIDTH = (890,)
POPUP_LIVE_SCROLL_HEIGHT = 700

MAPPER_PREVIEW_MAX_HEIGHT = 100
MAPPER_PREVIEW_MAX_WIDTH = 100

DEFAULT_BUTTON_WIDTH = 200
DEFAULT_BUTTON_HEIGHT = 40

RECENT_DIRECTORY_SOURCE = None
RECENT_DIRECTORY_TARGET = None
RECENT_DIRECTORY_OUTPUT = None

_ = None
preview_label = None
preview_slider = None
preview_nav_frame = None
preview_prev_button = None
preview_next_button = None
preview_file_label = None
preview_current_index = 0
preview_is_closing = False  # Flag to prevent reopening loop
source_label = None
target_label = None
status_label = None
popup_status_label = None
popup_status_label_live = None
source_label_dict = {}
source_label_dict_live = {}
target_label_dict_live = {}

img_ft, vid_ft = modules.globals.file_types


def init(start: Callable[[], None], destroy: Callable[[], None], lang: str) -> ctk.CTk:
    global ROOT, PREVIEW, _

    lang_manager = LanguageManager(lang)
    _ = lang_manager._
    ROOT = create_root(start, destroy)
    PREVIEW = create_preview(ROOT)

    return ROOT


def save_switch_states():
    switch_states = {
        "keep_fps": modules.globals.keep_fps,
        "keep_audio": modules.globals.keep_audio,
        "keep_frames": modules.globals.keep_frames,
        "many_faces": modules.globals.many_faces,
        "map_faces": modules.globals.map_faces,
        "color_correction": modules.globals.color_correction,
        "nsfw_filter": modules.globals.nsfw_filter,
        "live_mirror": modules.globals.live_mirror,
        "live_resizable": modules.globals.live_resizable,
        "fp_ui": modules.globals.fp_ui,
        "show_fps": modules.globals.show_fps,
        "mouth_mask": modules.globals.mouth_mask,
        "show_mouth_mask_box": modules.globals.show_mouth_mask_box,
        "process_folder": modules.globals.process_folder,
        "vps_enabled": modules.globals.vps_enabled,
        "vps_server_url": modules.globals.vps_server_url,
    }
    with open("switch_states.json", "w") as f:
        json.dump(switch_states, f)


def load_switch_states():
    try:
        with open("switch_states.json", "r") as f:
            switch_states = json.load(f)
        modules.globals.keep_fps = switch_states.get("keep_fps", True)
        modules.globals.keep_audio = switch_states.get("keep_audio", True)
        modules.globals.keep_frames = switch_states.get("keep_frames", False)
        modules.globals.many_faces = switch_states.get("many_faces", False)
        modules.globals.map_faces = switch_states.get("map_faces", False)
        modules.globals.color_correction = switch_states.get("color_correction", False)
        modules.globals.nsfw_filter = switch_states.get("nsfw_filter", False)
        modules.globals.live_mirror = switch_states.get("live_mirror", False)
        modules.globals.live_resizable = switch_states.get("live_resizable", False)
        modules.globals.fp_ui = switch_states.get("fp_ui", {"face_enhancer": False})
        modules.globals.show_fps = switch_states.get("show_fps", False)
        modules.globals.mouth_mask = switch_states.get("mouth_mask", False)
        modules.globals.show_mouth_mask_box = switch_states.get(
            "show_mouth_mask_box", False
        )
        modules.globals.process_folder = switch_states.get("process_folder", False)
        modules.globals.vps_enabled = switch_states.get("vps_enabled", False)
        modules.globals.vps_server_url = switch_states.get("vps_server_url", None)
    except FileNotFoundError:
        # If the file doesn't exist, use default values
        pass


def create_root(start: Callable[[], None], destroy: Callable[[], None]) -> ctk.CTk:
    global source_label, target_label, status_label, show_fps_switch

    load_switch_states()

    ctk.deactivate_automatic_dpi_awareness()
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme(resolve_relative_path("ui.json"))

    root = ctk.CTk()
    root.minsize(ROOT_WIDTH, ROOT_HEIGHT)
    root.title(
        f"{modules.metadata.name} {modules.metadata.version} {modules.metadata.edition}"
    )
    root.configure()
    root.protocol("WM_DELETE_WINDOW", lambda: destroy())

    # Criar TabView para abas
    tabview = ctk.CTkTabview(root, width=ROOT_WIDTH-20, height=ROOT_HEIGHT-100)
    tabview.place(relx=0.02, rely=0.02, relwidth=0.96, relheight=0.85)
    
    # Aba 1: Processamento Principal
    tab_processamento = tabview.add(_("Processamento"))
    
    # Aba 2: Configurações e VPS
    tab_config = tabview.add(_("Configurações"))

    # ========== ABA 1: PROCESSAMENTO ==========
    source_label = ctk.CTkLabel(tab_processamento, text=None)
    source_label.place(relx=0.1, rely=0.05, relwidth=0.275, relheight=0.225)

    target_label = ctk.CTkLabel(tab_processamento, text=None)
    target_label.place(relx=0.6, rely=0.05, relwidth=0.275, relheight=0.225)

    select_face_button = ctk.CTkButton(
        tab_processamento, text=_("Select a face"), cursor="hand2", command=lambda: select_source_path()
    )
    select_face_button.place(relx=0.1, rely=0.30, relwidth=0.3, relheight=0.1)

    swap_faces_button = ctk.CTkButton(
        tab_processamento, text="↔", cursor="hand2", command=lambda: swap_faces_paths()
    )
    swap_faces_button.place(relx=0.45, rely=0.30, relwidth=0.1, relheight=0.1)


    select_target_button = ctk.CTkButton(
        tab_processamento,
        text=_("Select a target"),
        cursor="hand2",
        command=lambda: select_target_path(),
    )
    select_target_button.place(relx=0.6, rely=0.30, relwidth=0.3, relheight=0.1)

    keep_fps_value = ctk.BooleanVar(value=modules.globals.keep_fps)
    keep_fps_checkbox = ctk.CTkSwitch(
        tab_processamento,
        text=_("Keep fps"),
        variable=keep_fps_value,
        cursor="hand2",
        command=lambda: (
            setattr(modules.globals, "keep_fps", keep_fps_value.get()),
            save_switch_states(),
        ),
    )
    keep_fps_checkbox.place(relx=0.1, rely=0.45)

    keep_audio_value = ctk.BooleanVar(value=modules.globals.keep_audio)
    keep_audio_switch = ctk.CTkSwitch(
        tab_processamento,
        text=_("Keep audio"),
        variable=keep_audio_value,
        cursor="hand2",
        command=lambda: (
            setattr(modules.globals, "keep_audio", keep_audio_value.get()),
            save_switch_states(),
        ),
    )
    keep_audio_switch.place(relx=0.6, rely=0.45)

    many_faces_value = ctk.BooleanVar(value=modules.globals.many_faces)
    many_faces_switch = ctk.CTkSwitch(
        tab_processamento,
        text=_("Many faces"),
        variable=many_faces_value,
        cursor="hand2",
        command=lambda: (
            setattr(modules.globals, "many_faces", many_faces_value.get()),
            save_switch_states(),
        ),
    )
    many_faces_switch.place(relx=0.1, rely=0.5)

    color_correction_value = ctk.BooleanVar(value=modules.globals.color_correction)
    color_correction_switch = ctk.CTkSwitch(
        tab_processamento,
        text=_("Fix Blueish Cam"),
        variable=color_correction_value,
        cursor="hand2",
        command=lambda: (
            setattr(modules.globals, "color_correction", color_correction_value.get()),
            save_switch_states(),
        ),
    )
    color_correction_switch.place(relx=0.6, rely=0.5)

    enhancer_value = ctk.BooleanVar(value=modules.globals.fp_ui["face_enhancer"])
    enhancer_switch = ctk.CTkSwitch(
        tab_processamento,
        text=_("Face Enhancer"),
        variable=enhancer_value,
        cursor="hand2",
        command=lambda: (
            update_tumbler("face_enhancer", enhancer_value.get()),
            save_switch_states(),
        ),
    )
    enhancer_switch.place(relx=0.1, rely=0.55)

    map_faces = ctk.BooleanVar(value=modules.globals.map_faces)
    map_faces_switch = ctk.CTkSwitch(
        tab_processamento,
        text=_("Map faces"),
        variable=map_faces,
        cursor="hand2",
        command=lambda: (
            setattr(modules.globals, "map_faces", map_faces.get()),
            save_switch_states(),
            close_mapper_window() if not map_faces.get() else None
        ),
    )
    map_faces_switch.place(relx=0.6, rely=0.55)

    mouth_mask_var = ctk.BooleanVar(value=modules.globals.mouth_mask)
    mouth_mask_switch = ctk.CTkSwitch(
        tab_processamento,
        text=_("Mouth Mask"),
        variable=mouth_mask_var,
        cursor="hand2",
        command=lambda: setattr(modules.globals, "mouth_mask", mouth_mask_var.get()),
    )
    mouth_mask_switch.place(relx=0.1, rely=0.6)

    show_mouth_mask_box_var = ctk.BooleanVar(value=modules.globals.show_mouth_mask_box)
    show_mouth_mask_box_switch = ctk.CTkSwitch(
        tab_processamento,
        text=_("Show Mouth Mask Box"),
        variable=show_mouth_mask_box_var,
        cursor="hand2",
        command=lambda: setattr(
            modules.globals, "show_mouth_mask_box", show_mouth_mask_box_var.get()
        ),
    )
    show_mouth_mask_box_switch.place(relx=0.6, rely=0.6)

    # Sliders na aba principal
    transparency_var = ctk.DoubleVar(value=1.0)

    def on_transparency_change(value: float):
        val = float(value)
        modules.globals.opacity = val
        percentage = int(val * 100)
        if percentage == 0:
            modules.globals.fp_ui["face_enhancer"] = False
            update_status(_("Transparency set to 0% - Face swapping disabled."))
        elif percentage == 100:
            modules.globals.face_swapper_enabled = True
            update_status(_("Transparency set to 100%."))
        else:
            modules.globals.face_swapper_enabled = True
            update_status(_("Transparency set to {percentage}%").format(percentage=percentage))

    transparency_label = ctk.CTkLabel(tab_processamento, text=_("Transparency:"))
    transparency_label.place(relx=0.1, rely=0.65, relwidth=0.2, relheight=0.04)

    transparency_slider = ctk.CTkSlider(
        tab_processamento,
        from_=0.0,
        to=1.0,
        variable=transparency_var,
        command=on_transparency_change,
        fg_color="#E0E0E0",
        progress_color="#007BFF",
        button_color="#FFFFFF",
        button_hover_color="#CCCCCC",
        height=5,
        border_width=1,
        corner_radius=3,
    )
    transparency_slider.place(relx=0.3, rely=0.67, relwidth=0.6, relheight=0.02)

    sharpness_var = ctk.DoubleVar(value=0.0)
    def on_sharpness_change(value: float):
        modules.globals.sharpness = float(value)
        update_status(f"Sharpness set to {value:.1f}")

    sharpness_label = ctk.CTkLabel(tab_processamento, text=_("Sharpness:"))
    sharpness_label.place(relx=0.1, rely=0.7, relwidth=0.2, relheight=0.04)

    sharpness_slider = ctk.CTkSlider(
        tab_processamento,
        from_=0.0,
        to=5.0,
        variable=sharpness_var,
        command=on_sharpness_change,
        fg_color="#E0E0E0",
        progress_color="#007BFF",
        button_color="#FFFFFF",
        button_hover_color="#CCCCCC",
        height=5,
        border_width=1,
        corner_radius=3,
    )
    sharpness_slider.place(relx=0.3, rely=0.72, relwidth=0.6, relheight=0.02)

    # Botões principais na aba de processamento
    start_button = ctk.CTkButton(
        tab_processamento, text=_("Start"), cursor="hand2", command=lambda: analyze_target(start, root)
    )
    start_button.place(relx=0.15, rely=0.78, relwidth=0.2, relheight=0.08)

    stop_button = ctk.CTkButton(
        tab_processamento, text=_("Destroy"), cursor="hand2", command=lambda: destroy()
    )
    stop_button.place(relx=0.4, rely=0.78, relwidth=0.2, relheight=0.08)

    preview_button = ctk.CTkButton(
        tab_processamento, text=_("Preview"), cursor="hand2", command=lambda: toggle_preview()
    )
    preview_button.place(relx=0.65, rely=0.78, relwidth=0.2, relheight=0.08)

    # ========== ABA 2: CONFIGURAÇÕES ==========
    
    # Processar pasta
    process_folder_value = ctk.BooleanVar(value=modules.globals.process_folder)
    process_folder_switch = ctk.CTkSwitch(
        tab_config,
        text=_("Process folder"),
        variable=process_folder_value,
        cursor="hand2",
        command=lambda: (
            setattr(modules.globals, "process_folder", process_folder_value.get()),
            save_switch_states(),
        ),
    )
    process_folder_switch.place(relx=0.1, rely=0.05)

    # VPS Remote Processing
    vps_label = ctk.CTkLabel(tab_config, text=_("=== GPU Externa (VPS) ==="), font=("Arial", 14, "bold"))
    vps_label.place(relx=0.1, rely=0.15, relwidth=0.8)
    
    vps_enabled_value = ctk.BooleanVar(value=modules.globals.vps_enabled)
    vps_switch = ctk.CTkSwitch(
        tab_config,
        text=_("Habilitar GPU Externa (VPS)"),
        variable=vps_enabled_value,
        cursor="hand2",
        command=lambda: (
            setattr(modules.globals, "vps_enabled", vps_enabled_value.get()),
            save_switch_states(),
        ),
    )
    vps_switch.place(relx=0.1, rely=0.22)
    
    # VPS Server URL
    vps_url_label = ctk.CTkLabel(tab_config, text=_("Servidor VPS:"))
    vps_url_label.place(relx=0.1, rely=0.28, relwidth=0.2, relheight=0.04)
    
    vps_url_entry = ctk.CTkEntry(
        tab_config,
        placeholder_text="192.168.1.100:8765",
        width=250
    )
    if modules.globals.vps_server_url:
        vps_url_entry.insert(0, modules.globals.vps_server_url)
    vps_url_entry.place(relx=0.1, rely=0.33, relwidth=0.4, relheight=0.04)
    
    def save_vps_url():
        url = vps_url_entry.get().strip()
        if url:
            modules.globals.vps_server_url = url
            update_status(f"Servidor VPS salvo: {url}")
        else:
            modules.globals.vps_server_url = None
            update_status("Servidor VPS removido")
        save_switch_states()
    
    # Botão para salvar URL
    save_vps_button = ctk.CTkButton(
        tab_config,
        text=_("Salvar IP"),
        cursor="hand2",
        command=save_vps_url,
        width=80,
        height=25
    )
    save_vps_button.place(relx=0.52, rely=0.33, relwidth=0.15, relheight=0.04)
    
    # Botão para testar conexão
    def test_vps_connection():
        url = vps_url_entry.get().strip()
        if not url:
            update_status("Por favor, informe a URL do servidor VPS")
            return
        
        try:
            import websockets
        except ImportError:
            update_status("❌ Módulo 'websockets' não instalado. Execute: pip install websockets")
            return
        
        try:
            from modules.vps.client_ws import VPSClient
            client = VPSClient(url)
            sucesso, mensagem = client.test_connection_sync()
            if sucesso:
                update_status(f"✅ {mensagem}")
            else:
                update_status(f"❌ {mensagem}")
        except ImportError as e:
            update_status(f"❌ Erro de importação: {str(e)}. Instale: pip install websockets")
        except Exception as e:
            update_status(f"❌ Erro ao testar conexão: {str(e)}")
    
    test_vps_button = ctk.CTkButton(
        tab_config,
        text=_("Testar Conexão"),
        cursor="hand2",
        command=test_vps_connection,
        width=100,
        height=25
    )
    test_vps_button.place(relx=0.68, rely=0.33, relwidth=0.2, relheight=0.04)
    
    vps_info_label = ctk.CTkLabel(
        tab_config, 
        text=_("Exemplo: 192.168.1.100:8765 ou IP_PUBLICO:8765"),
        font=("Arial", 10),
        text_color="gray"
    )
    vps_info_label.place(relx=0.1, rely=0.38, relwidth=0.8)

    # --- Camera Selection (na aba de processamento) ---
    camera_label = ctk.CTkLabel(tab_processamento, text=_("Select Camera:"))
    camera_label.place(relx=0.1, rely=0.85, relwidth=0.2, relheight=0.05)

    available_cameras = get_available_cameras()
    camera_indices, camera_names = available_cameras

    if not camera_names or camera_names[0] == "No cameras found":
        camera_variable = ctk.StringVar(value="No cameras found")
        camera_optionmenu = ctk.CTkOptionMenu(
            tab_processamento,
            variable=camera_variable,
            values=["No cameras found"],
            state="disabled",
        )
    else:
        camera_variable = ctk.StringVar(value=camera_names[0])
        camera_optionmenu = ctk.CTkOptionMenu(
            tab_processamento, variable=camera_variable, values=camera_names
        )

    camera_optionmenu.place(relx=0.35, rely=0.85, relwidth=0.25, relheight=0.05)

    live_button = ctk.CTkButton(
        tab_processamento,
        text=_("Live"),
        cursor="hand2",
        command=lambda: webcam_preview(
            root,
            (
                camera_indices[camera_names.index(camera_variable.get())]
                if camera_names and camera_names[0] != "No cameras found"
                else None
            ),
        ),
        state=(
            "normal"
            if camera_names and camera_names[0] != "No cameras found"
            else "disabled"
        ),
    )
    live_button.place(relx=0.65, rely=0.85, relwidth=0.2, relheight=0.05)
    # --- End Camera Selection ---


    # Status and link at the bottom (fora das abas)
    global status_label
    status_label = ctk.CTkLabel(root, text=None, justify="center")
    status_label.place(relx=0.1, rely=0.88, relwidth=0.8)

    donate_label = ctk.CTkLabel(
        root, text="Deep Live Cam", justify="center", cursor="hand2"
    )
    donate_label.place(relx=0.1, rely=0.93, relwidth=0.8)
    donate_label.configure(
        text_color=ctk.ThemeManager.theme.get("URL").get("text_color")
    )
    donate_label.bind(
        "<Button>", lambda event: webbrowser.open("https://deeplivecam.net")
    )

    return root


def close_mapper_window():
    global POPUP, POPUP_LIVE
    if POPUP and POPUP.winfo_exists():
        POPUP.destroy()
        POPUP = None
    if POPUP_LIVE and POPUP_LIVE.winfo_exists():
        POPUP_LIVE.destroy()
        POPUP_LIVE = None


def analyze_target(start: Callable[[], None], root: ctk.CTk):
    if POPUP != None and POPUP.winfo_exists():
        update_status("Please complete pop-up or close it.")
        return

    # Check if processing folder mode
    if modules.globals.process_folder and modules.globals.file_queue:
        if not modules.globals.source_path:
            update_status("Please select a source image first")
            return
        # Skip face mapping for folder processing (use default source for all)
        # Output directory will be selected in start() function
        start()
        return

    if modules.globals.map_faces:
        modules.globals.source_target_map = []

        if is_image(modules.globals.target_path):
            update_status("Getting unique faces")
            get_unique_faces_from_target_image()
        elif is_video(modules.globals.target_path):
            update_status("Getting unique faces")
            get_unique_faces_from_target_video()

        if len(modules.globals.source_target_map) > 0:
            create_source_target_popup(start, root, modules.globals.source_target_map)
        else:
            update_status("No faces found in target")
    else:
        select_output_path(start)


def create_source_target_popup(
        start: Callable[[], None], root: ctk.CTk, map: list
) -> None:
    global POPUP, popup_status_label

    POPUP = ctk.CTkToplevel(root)
    POPUP.title(_("Source x Target Mapper"))
    POPUP.geometry(f"{POPUP_WIDTH}x{POPUP_HEIGHT}")
    POPUP.focus()

    def on_submit_click(start):
        if has_valid_map():
            POPUP.destroy()
            select_output_path(start)
        else:
            update_pop_status("Atleast 1 source with target is required!")

    scrollable_frame = ctk.CTkScrollableFrame(
        POPUP, width=POPUP_SCROLL_WIDTH, height=POPUP_SCROLL_HEIGHT
    )
    scrollable_frame.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")

    def on_button_click(map, button_num):
        map = update_popup_source(scrollable_frame, map, button_num)

    for item in map:
        id = item["id"]

        button = ctk.CTkButton(
            scrollable_frame,
            text=_("Select source image"),
            command=lambda id=id: on_button_click(map, id),
            width=DEFAULT_BUTTON_WIDTH,
            height=DEFAULT_BUTTON_HEIGHT,
        )
        button.grid(row=id, column=0, padx=50, pady=10)

        x_label = ctk.CTkLabel(
            scrollable_frame,
            text=f"X",
            width=MAPPER_PREVIEW_MAX_WIDTH,
            height=MAPPER_PREVIEW_MAX_HEIGHT,
        )
        x_label.grid(row=id, column=2, padx=10, pady=10)

        image = Image.fromarray(cv2.cvtColor(item["target"]["cv2"], cv2.COLOR_BGR2RGB))
        image = image.resize(
            (MAPPER_PREVIEW_MAX_WIDTH, MAPPER_PREVIEW_MAX_HEIGHT), Image.LANCZOS
        )
        tk_image = ctk.CTkImage(image, size=image.size)

        target_image = ctk.CTkLabel(
            scrollable_frame,
            text=f"T-{id}",
            width=MAPPER_PREVIEW_MAX_WIDTH,
            height=MAPPER_PREVIEW_MAX_HEIGHT,
        )
        target_image.grid(row=id, column=3, padx=10, pady=10)
        target_image.configure(image=tk_image)

    popup_status_label = ctk.CTkLabel(POPUP, text=None, justify="center")
    popup_status_label.grid(row=1, column=0, pady=15)

    close_button = ctk.CTkButton(
        POPUP, text=_("Submit"), command=lambda: on_submit_click(start)
    )
    close_button.grid(row=2, column=0, pady=10)


def update_popup_source(
        scrollable_frame: ctk.CTkScrollableFrame, map: list, button_num: int
) -> list:
    global source_label_dict

    source_path = ctk.filedialog.askopenfilename(
        title=_("select an source image"),
        initialdir=RECENT_DIRECTORY_SOURCE,
        filetypes=[img_ft],
    )

    if "source" in map[button_num]:
        map[button_num].pop("source")
        source_label_dict[button_num].destroy()
        del source_label_dict[button_num]

    if source_path == "":
        return map
    else:
        cv2_img = cv2.imread(source_path)
        face = get_one_face(cv2_img)

        if face:
            x_min, y_min, x_max, y_max = face["bbox"]

            map[button_num]["source"] = {
                "cv2": cv2_img[int(y_min): int(y_max), int(x_min): int(x_max)],
                "face": face,
            }

            image = Image.fromarray(
                cv2.cvtColor(map[button_num]["source"]["cv2"], cv2.COLOR_BGR2RGB)
            )
            image = image.resize(
                (MAPPER_PREVIEW_MAX_WIDTH, MAPPER_PREVIEW_MAX_HEIGHT), Image.LANCZOS
            )
            tk_image = ctk.CTkImage(image, size=image.size)

            source_image = ctk.CTkLabel(
                scrollable_frame,
                text=f"S-{button_num}",
                width=MAPPER_PREVIEW_MAX_WIDTH,
                height=MAPPER_PREVIEW_MAX_HEIGHT,
            )
            source_image.grid(row=button_num, column=1, padx=10, pady=10)
            source_image.configure(image=tk_image)
            source_label_dict[button_num] = source_image
        else:
            update_pop_status("Face could not be detected in last upload!")
        return map


def create_preview(parent: ctk.CTkToplevel) -> ctk.CTkToplevel:
    global preview_label, preview_slider, preview_nav_frame, preview_prev_button
    global preview_next_button, preview_file_label

    preview = ctk.CTkToplevel(parent)
    preview.withdraw()
    preview.title(_("Preview"))
    preview.configure()
    
    def close_preview():
        """Handle preview window close event."""
        global preview_is_closing
        preview_is_closing = True
        preview.withdraw()
        # Reset flag after delay to allow normal reopening
        def reset_flag():
            global preview_is_closing
            preview_is_closing = False
        preview.after(100, reset_flag)
    
    preview.protocol("WM_DELETE_WINDOW", close_preview)
    preview.resizable(width=True, height=True)

    preview_label = ctk.CTkLabel(preview, text=None)
    preview_label.pack(fill="both", expand=True)

    # Navigation frame for folder preview
    preview_nav_frame = ctk.CTkFrame(preview)
    
    preview_prev_button = ctk.CTkButton(
        preview_nav_frame,
        text="◀ Previous",
        command=lambda: navigate_preview_folder(-1),
        width=120
    )
    preview_prev_button.pack(side="left", padx=5, pady=5)
    
    preview_file_label = ctk.CTkLabel(
        preview_nav_frame,
        text="",
        width=300
    )
    preview_file_label.pack(side="left", padx=10, pady=5)
    
    preview_next_button = ctk.CTkButton(
        preview_nav_frame,
        text="Next ▶",
        command=lambda: navigate_preview_folder(1),
        width=120
    )
    preview_next_button.pack(side="left", padx=5, pady=5)

    preview_slider = ctk.CTkSlider(
        preview, from_=0, to=0, command=lambda frame_value: update_preview(frame_value)
    )

    return preview


def update_status(text: str) -> None:
    status_label.configure(text=_(text))
    ROOT.update()


def update_pop_status(text: str) -> None:
    popup_status_label.configure(text=_(text))


def update_pop_live_status(text: str) -> None:
    popup_status_label_live.configure(text=_(text))


def update_tumbler(var: str, value: bool) -> None:
    modules.globals.fp_ui[var] = value
    save_switch_states()
    # If we're currently in a live preview, update the frame processors
    if PREVIEW.state() == "normal":
        global frame_processors
        frame_processors = get_frame_processors_modules(
            modules.globals.frame_processors
        )


def select_source_path() -> None:
    global RECENT_DIRECTORY_SOURCE, img_ft, vid_ft

    PREVIEW.withdraw()
    source_path = ctk.filedialog.askopenfilename(
        title=_("select an source image"),
        initialdir=RECENT_DIRECTORY_SOURCE,
        filetypes=[img_ft],
    )
    if is_image(source_path):
        modules.globals.source_path = source_path
        RECENT_DIRECTORY_SOURCE = os.path.dirname(modules.globals.source_path)
        image = render_image_preview(modules.globals.source_path, (200, 200))
        source_label.configure(image=image)
    else:
        modules.globals.source_path = None
        source_label.configure(image=None)


def swap_faces_paths() -> None:
    global RECENT_DIRECTORY_SOURCE, RECENT_DIRECTORY_TARGET

    source_path = modules.globals.source_path
    target_path = modules.globals.target_path

    if not is_image(source_path) or not is_image(target_path):
        return

    modules.globals.source_path = target_path
    modules.globals.target_path = source_path

    RECENT_DIRECTORY_SOURCE = os.path.dirname(modules.globals.source_path)
    RECENT_DIRECTORY_TARGET = os.path.dirname(modules.globals.target_path)

    PREVIEW.withdraw()

    source_image = render_image_preview(modules.globals.source_path, (200, 200))
    source_label.configure(image=source_image)

    target_image = render_image_preview(modules.globals.target_path, (200, 200))
    target_label.configure(image=target_image)


def select_target_path() -> None:
    global RECENT_DIRECTORY_TARGET, img_ft, vid_ft

    PREVIEW.withdraw()
    
    # If process_folder is enabled, allow folder selection
    if modules.globals.process_folder:
        folder_path = ctk.filedialog.askdirectory(
            title=_("select a folder with images or videos"),
            initialdir=RECENT_DIRECTORY_TARGET,
        )
        if folder_path:
            modules.globals.folder_path = folder_path
            RECENT_DIRECTORY_TARGET = folder_path
            # List valid files in folder
            valid_files = get_valid_files_from_folder(folder_path)
            if valid_files:
                modules.globals.file_queue = valid_files
                update_status(_("Found {count} files to process").format(count=len(valid_files)))
                # Show preview of first file
                first_file = valid_files[0]
                if is_image(first_file):
                    image = render_image_preview(first_file, (200, 200))
                    target_label.configure(image=image)
                elif is_video(first_file):
                    video_frame = render_video_preview(first_file, (200, 200))
                    target_label.configure(image=video_frame)
            else:
                update_status(_("No valid image or video files found in folder"))
                modules.globals.folder_path = None
                modules.globals.file_queue = []
                target_label.configure(image=None)
        else:
            modules.globals.folder_path = None
            modules.globals.file_queue = []
            target_label.configure(image=None)
    else:
        # Normal file selection
        target_path = ctk.filedialog.askopenfilename(
            title=_("select an target image or video"),
            initialdir=RECENT_DIRECTORY_TARGET,
            filetypes=[img_ft, vid_ft],
        )
        if is_image(target_path):
            modules.globals.target_path = target_path
            RECENT_DIRECTORY_TARGET = os.path.dirname(modules.globals.target_path)
            image = render_image_preview(modules.globals.target_path, (200, 200))
            target_label.configure(image=image)
        elif is_video(target_path):
            modules.globals.target_path = target_path
            RECENT_DIRECTORY_TARGET = os.path.dirname(modules.globals.target_path)
            video_frame = render_video_preview(target_path, (200, 200))
            target_label.configure(image=video_frame)
        else:
            modules.globals.target_path = None
            target_label.configure(image=None)


def select_output_directory() -> str | None:
    """Select output directory for folder processing mode."""
    global RECENT_DIRECTORY_OUTPUT
    output_dir = ctk.filedialog.askdirectory(
        title=_("select output directory"),
        initialdir=RECENT_DIRECTORY_OUTPUT,
    )
    if output_dir:
        RECENT_DIRECTORY_OUTPUT = output_dir
    return output_dir


def select_output_path(start: Callable[[], None]) -> None:
    global RECENT_DIRECTORY_OUTPUT, img_ft, vid_ft

    if is_image(modules.globals.target_path):
        output_path = ctk.filedialog.asksaveasfilename(
            title=_("save image output file"),
            filetypes=[img_ft],
            defaultextension=".png",
            initialfile="output.png",
            initialdir=RECENT_DIRECTORY_OUTPUT,
        )
    elif is_video(modules.globals.target_path):
        output_path = ctk.filedialog.asksaveasfilename(
            title=_("save video output file"),
            filetypes=[vid_ft],
            defaultextension=".mp4",
            initialfile="output.mp4",
            initialdir=RECENT_DIRECTORY_OUTPUT,
        )
    else:
        output_path = None
    if output_path:
        modules.globals.output_path = output_path
        RECENT_DIRECTORY_OUTPUT = os.path.dirname(modules.globals.output_path)
        start()


def check_and_ignore_nsfw(target, destroy: Callable = None) -> bool:
    """Check if the target is NSFW.
    TODO: Consider to make blur the target.
    """
    from numpy import ndarray
    from modules.predicter import predict_image, predict_video, predict_frame

    if type(target) is str:  # image/video file path
        check_nsfw = predict_image if has_image_extension(target) else predict_video
    elif type(target) is ndarray:  # frame object
        check_nsfw = predict_frame
    if check_nsfw and check_nsfw(target):
        if destroy:
            destroy(
                to_quit=False
            )  # Do not need to destroy the window frame if the target is NSFW
        update_status("Processing ignored!")
        return True
    else:
        return False


def fit_image_to_size(image, width: int, height: int):
    if width is None and height is None:
        return image
    h, w, _ = image.shape
    ratio_h = 0.0
    ratio_w = 0.0
    if width > height:
        ratio_h = height / h
    else:
        ratio_w = width / w
    ratio = max(ratio_w, ratio_h)
    new_size = (int(ratio * w), int(ratio * h))
    return cv2.resize(image, dsize=new_size)


def render_image_preview(image_path: str, size: Tuple[int, int]) -> ctk.CTkImage:
    image = Image.open(image_path)
    if size:
        image = ImageOps.fit(image, size, Image.LANCZOS)
    return ctk.CTkImage(image, size=image.size)


def render_video_preview(
        video_path: str, size: Tuple[int, int], frame_number: int = 0
) -> ctk.CTkImage:
    capture = cv2.VideoCapture(video_path)
    if frame_number:
        capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    has_frame, frame = capture.read()
    if has_frame:
        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        if size:
            image = ImageOps.fit(image, size, Image.LANCZOS)
        return ctk.CTkImage(image, size=image.size)
    capture.release()
    cv2.destroyAllWindows()


def toggle_preview() -> None:
    global preview_is_closing
    
    # Check if we're in the process of closing to prevent loop
    if preview_is_closing:
        return
    
    if PREVIEW.state() == "normal":
        # Set flag to prevent reopening
        preview_is_closing = True
        PREVIEW.withdraw()
        # Reset flag after a short delay to allow normal reopening later
        def reset_flag():
            global preview_is_closing
            preview_is_closing = False
        PREVIEW.after(100, reset_flag)
    elif modules.globals.source_path:
        # Reset flag when opening
        preview_is_closing = False
        if modules.globals.process_folder and modules.globals.file_queue:
            # Folder preview mode
            init_preview_folder()
            update_preview_folder(0)
        elif modules.globals.target_path:
            # Single file preview mode
            init_preview()
            update_preview()


def init_preview() -> None:
    # Hide folder navigation controls
    if preview_nav_frame:
        preview_nav_frame.pack_forget()
    
    if is_image(modules.globals.target_path):
        preview_slider.pack_forget()
    if is_video(modules.globals.target_path):
        video_frame_total = get_video_frame_total(modules.globals.target_path)
        preview_slider.configure(to=video_frame_total)
        preview_slider.pack(fill="x")
        preview_slider.set(0)


def init_preview_folder() -> None:
    """Initialize preview for folder mode with navigation controls."""
    global preview_current_index
    
    preview_current_index = 0
    
    # Show navigation controls
    if preview_nav_frame:
        preview_nav_frame.pack(fill="x", padx=5, pady=5, before=preview_label)
    
    # Hide video slider initially (will be shown if current file is video)
    preview_slider.pack_forget()
    
    # Update navigation buttons state
    update_navigation_buttons()


def navigate_preview_folder(direction: int) -> None:
    """Navigate to previous or next media in folder."""
    global preview_current_index
    
    if not modules.globals.file_queue:
        return
    
    preview_current_index += direction
    
    # Clamp index to valid range
    if preview_current_index < 0:
        preview_current_index = 0
    elif preview_current_index >= len(modules.globals.file_queue):
        preview_current_index = len(modules.globals.file_queue) - 1
    
    update_preview_folder(preview_current_index)


def update_navigation_buttons() -> None:
    """Update navigation buttons state based on current index."""
    if not preview_prev_button or not preview_next_button:
        return
    
    total_files = len(modules.globals.file_queue) if modules.globals.file_queue else 0
    
    # Enable/disable buttons based on position
    preview_prev_button.configure(state="normal" if preview_current_index > 0 else "disabled")
    preview_next_button.configure(state="normal" if preview_current_index < total_files - 1 else "disabled")


def update_preview_folder(file_index: int = 0) -> None:
    """Update preview for a specific file in the folder queue."""
    global preview_current_index
    
    if not modules.globals.source_path or not modules.globals.file_queue:
        return
    
    if file_index < 0 or file_index >= len(modules.globals.file_queue):
        return
    
    preview_current_index = file_index
    current_file = modules.globals.file_queue[file_index]
    
    # Update file label
    if preview_file_label:
        file_name = os.path.basename(current_file)
        total_files = len(modules.globals.file_queue)
        preview_file_label.configure(text=f"{file_name} ({file_index + 1}/{total_files})")
    
    # Update navigation buttons
    update_navigation_buttons()
    
    update_status("Processing preview...")
    
    try:
        # Process the current file for preview
        if is_image(current_file):
            # For images, process directly
            temp_frame = cv2.imread(current_file)
            if temp_frame is None:
                update_status(f"Error reading image: {current_file}")
                return
            
            if modules.globals.nsfw_filter and check_and_ignore_nsfw(temp_frame):
                return
            
            # Process with frame processors
            for frame_processor in get_frame_processors_modules(modules.globals.frame_processors):
                source_face = get_one_face(cv2.imread(modules.globals.source_path))
                temp_frame = frame_processor.process_frame(source_face, temp_frame)
            
            image = Image.fromarray(cv2.cvtColor(temp_frame, cv2.COLOR_BGR2RGB))
            image = ImageOps.contain(
                image, (PREVIEW_MAX_WIDTH, PREVIEW_MAX_HEIGHT), Image.LANCZOS
            )
            image = ctk.CTkImage(image, size=image.size)
            preview_label.configure(image=image)
            
            # Hide slider for images
            preview_slider.pack_forget()
            
        elif is_video(current_file):
            # For videos, show first frame
            temp_frame = get_video_frame(current_file, 0)
            if temp_frame is None:
                update_status(f"Error reading video: {current_file}")
                return
            
            if modules.globals.nsfw_filter and check_and_ignore_nsfw(temp_frame):
                return
            
            # Process with frame processors
            for frame_processor in get_frame_processors_modules(modules.globals.frame_processors):
                source_face = get_one_face(cv2.imread(modules.globals.source_path))
                temp_frame = frame_processor.process_frame(source_face, temp_frame)
            
            image = Image.fromarray(cv2.cvtColor(temp_frame, cv2.COLOR_BGR2RGB))
            image = ImageOps.contain(
                image, (PREVIEW_MAX_WIDTH, PREVIEW_MAX_HEIGHT), Image.LANCZOS
            )
            image = ctk.CTkImage(image, size=image.size)
            preview_label.configure(image=image)
            
            # Show slider for video
            video_frame_total = get_video_frame_total(current_file)
            if video_frame_total > 0:
                preview_slider.configure(to=video_frame_total)
                preview_slider.pack(fill="x", padx=5, pady=5, after=preview_nav_frame)
                preview_slider.set(0)
                # Update slider command to work with folder mode
                preview_slider.configure(command=lambda frame_value: update_preview_folder_video(frame_value))
            else:
                preview_slider.pack_forget()
        else:
            # Hide slider for non-video files
            preview_slider.pack_forget()
        
        update_status("Preview ready!")
        # Only show preview if not closing
        if not preview_is_closing:
            PREVIEW.deiconify()
        
    except Exception as e:
        update_status(f"Error processing preview: {str(e)}")


def update_preview_folder_video(frame_number: int = 0) -> None:
    """Update preview for video frame in folder mode."""
    if not modules.globals.source_path or not modules.globals.file_queue:
        return
    
    if preview_current_index < 0 or preview_current_index >= len(modules.globals.file_queue):
        return
    
    current_file = modules.globals.file_queue[preview_current_index]
    
    if not is_video(current_file):
        return
    
    try:
        temp_frame = get_video_frame(current_file, int(frame_number))
        if temp_frame is None:
            return
        
        if modules.globals.nsfw_filter and check_and_ignore_nsfw(temp_frame):
            return
        
        # Process with frame processors
        for frame_processor in get_frame_processors_modules(modules.globals.frame_processors):
            source_face = get_one_face(cv2.imread(modules.globals.source_path))
            temp_frame = frame_processor.process_frame(source_face, temp_frame)
        
        image = Image.fromarray(cv2.cvtColor(temp_frame, cv2.COLOR_BGR2RGB))
        image = ImageOps.contain(
            image, (PREVIEW_MAX_WIDTH, PREVIEW_MAX_HEIGHT), Image.LANCZOS
        )
        image = ctk.CTkImage(image, size=image.size)
        preview_label.configure(image=image)
        
    except Exception as e:
        update_status(f"Error updating video preview: {str(e)}")


def update_preview(frame_number: int = 0) -> None:
    if modules.globals.source_path and modules.globals.target_path:
        update_status("Processing...")
        temp_frame = get_video_frame(modules.globals.target_path, frame_number)
        if modules.globals.nsfw_filter and check_and_ignore_nsfw(temp_frame):
            return
        for frame_processor in get_frame_processors_modules(
                modules.globals.frame_processors
        ):
            temp_frame = frame_processor.process_frame(
                get_one_face(cv2.imread(modules.globals.source_path)), temp_frame
            )
        image = Image.fromarray(cv2.cvtColor(temp_frame, cv2.COLOR_BGR2RGB))
        image = ImageOps.contain(
            image, (PREVIEW_MAX_WIDTH, PREVIEW_MAX_HEIGHT), Image.LANCZOS
        )
        image = ctk.CTkImage(image, size=image.size)
        preview_label.configure(image=image)
        update_status("Processing succeed!")
        # Only show preview if not closing
        if not preview_is_closing:
            PREVIEW.deiconify()


def webcam_preview(root: ctk.CTk, camera_index: int):
    global POPUP_LIVE

    if POPUP_LIVE and POPUP_LIVE.winfo_exists():
        update_status("Source x Target Mapper is already open.")
        POPUP_LIVE.focus()
        return

    if not modules.globals.map_faces:
        if modules.globals.source_path is None:
            update_status("Please select a source image first")
            return
        create_webcam_preview(camera_index)
    else:
        modules.globals.source_target_map = []
        create_source_target_popup_for_webcam(
            root, modules.globals.source_target_map, camera_index
        )



def get_available_cameras():
    """Returns a list of available camera names and indices."""
    if platform.system() == "Windows":
        try:
            graph = FilterGraph()
            devices = graph.get_input_devices()

            # Create list of indices and names
            camera_indices = list(range(len(devices)))
            camera_names = devices

            # If no cameras found through DirectShow, try OpenCV fallback
            if not camera_names:
                # Try to open camera with index -1 and 0
                test_indices = [-1, 0]
                working_cameras = []

                for idx in test_indices:
                    cap = cv2.VideoCapture(idx)
                    if cap.isOpened():
                        working_cameras.append(f"Camera {idx}")
                        cap.release()

                if working_cameras:
                    return test_indices[: len(working_cameras)], working_cameras

            # If still no cameras found, return empty lists
            if not camera_names:
                return [], ["No cameras found"]

            return camera_indices, camera_names

        except Exception as e:
            print(f"Error detecting cameras: {str(e)}")
            return [], ["No cameras found"]
    else:
        # Unix-like systems (Linux/Mac) camera detection
        camera_indices = []
        camera_names = []

        if platform.system() == "Darwin":  # macOS specific handling
            # Try to open the default FaceTime camera first
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                camera_indices.append(0)
                camera_names.append("FaceTime Camera")
                cap.release()

            # On macOS, additional cameras typically use indices 1 and 2
            for i in [1, 2]:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    camera_indices.append(i)
                    camera_names.append(f"Camera {i}")
                    cap.release()
        else:
            # Linux camera detection - test first 10 indices
            for i in range(10):
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    camera_indices.append(i)
                    camera_names.append(f"Camera {i}")
                    cap.release()

        if not camera_names:
            return [], ["No cameras found"]

        return camera_indices, camera_names


def create_webcam_preview(camera_index: int):
    global preview_label, PREVIEW

    cap = VideoCapturer(camera_index)
    if not cap.start(PREVIEW_DEFAULT_WIDTH, PREVIEW_DEFAULT_HEIGHT, 60):
        update_status("Failed to start camera")
        return

    preview_label.configure(width=PREVIEW_DEFAULT_WIDTH, height=PREVIEW_DEFAULT_HEIGHT)
    # Only show preview if not closing (webcam preview)
    if not preview_is_closing:
        PREVIEW.deiconify()

    frame_processors = get_frame_processors_modules(modules.globals.frame_processors)
    source_image = None
    prev_time = time.time()
    fps_update_interval = 0.5
    frame_count = 0
    fps = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        temp_frame = frame.copy()

        if modules.globals.live_mirror:
            temp_frame = cv2.flip(temp_frame, 1)

        if modules.globals.live_resizable:
            temp_frame = fit_image_to_size(
                temp_frame, PREVIEW.winfo_width(), PREVIEW.winfo_height()
            )

        else:
            temp_frame = fit_image_to_size(
                temp_frame, PREVIEW.winfo_width(), PREVIEW.winfo_height()
            )

        if not modules.globals.map_faces:
            if source_image is None and modules.globals.source_path:
                source_image = get_one_face(cv2.imread(modules.globals.source_path))

            for frame_processor in frame_processors:
                if frame_processor.NAME == "DLC.FACE-ENHANCER":
                    if modules.globals.fp_ui["face_enhancer"]:
                        temp_frame = frame_processor.process_frame(None, temp_frame)
                else:
                    temp_frame = frame_processor.process_frame(source_image, temp_frame)
        else:
            modules.globals.target_path = None
            for frame_processor in frame_processors:
                if frame_processor.NAME == "DLC.FACE-ENHANCER":
                    if modules.globals.fp_ui["face_enhancer"]:
                        temp_frame = frame_processor.process_frame_v2(temp_frame)
                else:
                    temp_frame = frame_processor.process_frame_v2(temp_frame)

        # Calculate and display FPS
        current_time = time.time()
        frame_count += 1
        if current_time - prev_time >= fps_update_interval:
            fps = frame_count / (current_time - prev_time)
            frame_count = 0
            prev_time = current_time

        if modules.globals.show_fps:
            cv2.putText(
                temp_frame,
                f"FPS: {fps:.1f}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2,
            )

        image = cv2.cvtColor(temp_frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(image)
        image = ImageOps.contain(
            image, (temp_frame.shape[1], temp_frame.shape[0]), Image.LANCZOS
        )
        image = ctk.CTkImage(image, size=image.size)
        preview_label.configure(image=image)
        ROOT.update()

        if PREVIEW.state() == "withdrawn":
            break

    cap.release()
    PREVIEW.withdraw()


def create_source_target_popup_for_webcam(
        root: ctk.CTk, map: list, camera_index: int
) -> None:
    global POPUP_LIVE, popup_status_label_live

    POPUP_LIVE = ctk.CTkToplevel(root)
    POPUP_LIVE.title(_("Source x Target Mapper"))
    POPUP_LIVE.geometry(f"{POPUP_LIVE_WIDTH}x{POPUP_LIVE_HEIGHT}")
    POPUP_LIVE.focus()

    def on_submit_click():
        if has_valid_map():
            simplify_maps()
            update_pop_live_status("Mappings successfully submitted!")
            create_webcam_preview(camera_index)  # Open the preview window
        else:
            update_pop_live_status("At least 1 source with target is required!")

    def on_add_click():
        add_blank_map()
        refresh_data(map)
        update_pop_live_status("Please provide mapping!")

    def on_clear_click():
        clear_source_target_images(map)
        refresh_data(map)
        update_pop_live_status("All mappings cleared!")

    popup_status_label_live = ctk.CTkLabel(POPUP_LIVE, text=None, justify="center")
    popup_status_label_live.grid(row=1, column=0, pady=15)

    add_button = ctk.CTkButton(POPUP_LIVE, text=_("Add"), command=lambda: on_add_click())
    add_button.place(relx=0.1, rely=0.92, relwidth=0.2, relheight=0.05)

    clear_button = ctk.CTkButton(POPUP_LIVE, text=_("Clear"), command=lambda: on_clear_click())
    clear_button.place(relx=0.4, rely=0.92, relwidth=0.2, relheight=0.05)

    close_button = ctk.CTkButton(
        POPUP_LIVE, text=_("Submit"), command=lambda: on_submit_click()
    )
    close_button.place(relx=0.7, rely=0.92, relwidth=0.2, relheight=0.05)



def clear_source_target_images(map: list):
    global source_label_dict_live, target_label_dict_live

    for item in map:
        if "source" in item:
            del item["source"]
        if "target" in item:
            del item["target"]

    for button_num in list(source_label_dict_live.keys()):
        source_label_dict_live[button_num].destroy()
        del source_label_dict_live[button_num]

    for button_num in list(target_label_dict_live.keys()):
        target_label_dict_live[button_num].destroy()
        del target_label_dict_live[button_num]


def refresh_data(map: list):
    global POPUP_LIVE

    scrollable_frame = ctk.CTkScrollableFrame(
        POPUP_LIVE, width=POPUP_LIVE_SCROLL_WIDTH, height=POPUP_LIVE_SCROLL_HEIGHT
    )
    scrollable_frame.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")

    def on_sbutton_click(map, button_num):
        map = update_webcam_source(scrollable_frame, map, button_num)

    def on_tbutton_click(map, button_num):
        map = update_webcam_target(scrollable_frame, map, button_num)

    for item in map:
        id = item["id"]

        button = ctk.CTkButton(
            scrollable_frame,
            text=_("Select source image"),
            command=lambda id=id: on_sbutton_click(map, id),
            width=DEFAULT_BUTTON_WIDTH,
            height=DEFAULT_BUTTON_HEIGHT,
        )
        button.grid(row=id, column=0, padx=30, pady=10)

        x_label = ctk.CTkLabel(
            scrollable_frame,
            text=f"X",
            width=MAPPER_PREVIEW_MAX_WIDTH,
            height=MAPPER_PREVIEW_MAX_HEIGHT,
        )
        x_label.grid(row=id, column=2, padx=10, pady=10)

        button = ctk.CTkButton(
            scrollable_frame,
            text=_("Select target image"),
            command=lambda id=id: on_tbutton_click(map, id),
            width=DEFAULT_BUTTON_WIDTH,
            height=DEFAULT_BUTTON_HEIGHT,
        )
        button.grid(row=id, column=3, padx=20, pady=10)

        if "source" in item:
            image = Image.fromarray(
                cv2.cvtColor(item["source"]["cv2"], cv2.COLOR_BGR2RGB)
            )
            image = image.resize(
                (MAPPER_PREVIEW_MAX_WIDTH, MAPPER_PREVIEW_MAX_HEIGHT), Image.LANCZOS
            )
            tk_image = ctk.CTkImage(image, size=image.size)

            source_image = ctk.CTkLabel(
                scrollable_frame,
                text=f"S-{id}",
                width=MAPPER_PREVIEW_MAX_WIDTH,
                height=MAPPER_PREVIEW_MAX_HEIGHT,
            )
            source_image.grid(row=id, column=1, padx=10, pady=10)
            source_image.configure(image=tk_image)

        if "target" in item:
            image = Image.fromarray(
                cv2.cvtColor(item["target"]["cv2"], cv2.COLOR_BGR2RGB)
            )
            image = image.resize(
                (MAPPER_PREVIEW_MAX_WIDTH, MAPPER_PREVIEW_MAX_HEIGHT), Image.LANCZOS
            )
            tk_image = ctk.CTkImage(image, size=image.size)

            target_image = ctk.CTkLabel(
                scrollable_frame,
                text=f"T-{id}",
                width=MAPPER_PREVIEW_MAX_WIDTH,
                height=MAPPER_PREVIEW_MAX_HEIGHT,
            )
            target_image.grid(row=id, column=4, padx=20, pady=10)
            target_image.configure(image=tk_image)


def update_webcam_source(
        scrollable_frame: ctk.CTkScrollableFrame, map: list, button_num: int
) -> list:
    global source_label_dict_live

    source_path = ctk.filedialog.askopenfilename(
        title=_("select an source image"),
        initialdir=RECENT_DIRECTORY_SOURCE,
        filetypes=[img_ft],
    )

    if "source" in map[button_num]:
        map[button_num].pop("source")
        source_label_dict_live[button_num].destroy()
        del source_label_dict_live[button_num]

    if source_path == "":
        return map
    else:
        cv2_img = cv2.imread(source_path)
        face = get_one_face(cv2_img)

        if face:
            x_min, y_min, x_max, y_max = face["bbox"]

            map[button_num]["source"] = {
                "cv2": cv2_img[int(y_min): int(y_max), int(x_min): int(x_max)],
                "face": face,
            }

            image = Image.fromarray(
                cv2.cvtColor(map[button_num]["source"]["cv2"], cv2.COLOR_BGR2RGB)
            )
            image = image.resize(
                (MAPPER_PREVIEW_MAX_WIDTH, MAPPER_PREVIEW_MAX_HEIGHT), Image.LANCZOS
            )
            tk_image = ctk.CTkImage(image, size=image.size)

            source_image = ctk.CTkLabel(
                scrollable_frame,
                text=f"S-{button_num}",
                width=MAPPER_PREVIEW_MAX_WIDTH,
                height=MAPPER_PREVIEW_MAX_HEIGHT,
            )
            source_image.grid(row=button_num, column=1, padx=10, pady=10)
            source_image.configure(image=tk_image)
            source_label_dict_live[button_num] = source_image
        else:
            update_pop_live_status("Face could not be detected in last upload!")
        return map


def get_valid_files_from_folder(folder_path: str) -> list:
    """Get all valid image and video files from a folder."""
    valid_files = []
    if not os.path.isdir(folder_path):
        return valid_files
    
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            if is_image(file_path) or is_video(file_path):
                valid_files.append(file_path)
    
    # Sort files for consistent processing order
    valid_files.sort()
    return valid_files


def update_webcam_target(
        scrollable_frame: ctk.CTkScrollableFrame, map: list, button_num: int
) -> list:
    global target_label_dict_live

    target_path = ctk.filedialog.askopenfilename(
        title=_("select an target image"),
        initialdir=RECENT_DIRECTORY_SOURCE,
        filetypes=[img_ft],
    )

    if "target" in map[button_num]:
        map[button_num].pop("target")
        target_label_dict_live[button_num].destroy()
        del target_label_dict_live[button_num]

    if target_path == "":
        return map
    else:
        cv2_img = cv2.imread(target_path)
        face = get_one_face(cv2_img)

        if face:
            x_min, y_min, x_max, y_max = face["bbox"]

            map[button_num]["target"] = {
                "cv2": cv2_img[int(y_min): int(y_max), int(x_min): int(x_max)],
                "face": face,
            }

            image = Image.fromarray(
                cv2.cvtColor(map[button_num]["target"]["cv2"], cv2.COLOR_BGR2RGB)
            )
            image = image.resize(
                (MAPPER_PREVIEW_MAX_WIDTH, MAPPER_PREVIEW_MAX_HEIGHT), Image.LANCZOS
            )
            tk_image = ctk.CTkImage(image, size=image.size)

            target_image = ctk.CTkLabel(
                scrollable_frame,
                text=f"T-{button_num}",
                width=MAPPER_PREVIEW_MAX_WIDTH,
                height=MAPPER_PREVIEW_MAX_HEIGHT,
            )
            target_image.grid(row=button_num, column=4, padx=20, pady=10)
            target_image.configure(image=tk_image)
            target_label_dict_live[button_num] = target_image
        else:
            update_pop_live_status("Face could not be detected in last upload!")
        return map