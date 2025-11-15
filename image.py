from zoneinfo import ZoneInfo
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io
import gettext

from config import Config
from domain import ServerInfo

lang = gettext.translation('ts3-status', localedir='locales', languages=[Config.language], fallback=True)
lang.install()
_ = lang.gettext

COLORS = {
    "card_bg": "#1e1f22",
    "text_primary": "#f2f3f5",
    "text_secondary": "#b5bac1",
    "accent": "#5865f2",
    "green": "#23a559",
    "yellow": "#f0b232",
    "red": "#f23f43",
    "border": "#3f4248"
}

FONT_PATH = "./resources/gg_sans.ttf"

ICON_PATH_TALKING = 'resources/user_talking.png'
ICON_PATH_INPUT_MUTED = 'resources/input_muted.png'
ICON_PATH_OUTPUT_MUTED = 'resources/output_muted.png'
ICON_PATH_DEFAULT = 'resources/user.png'

TEXT_ERROR_TITLE = _("TeamSpeak Server Unavailable")
TEXT_ERROR_PREFIX = _("Error: ")
TEXT_USERS_ONLINE = _("Users Online:")
TEXT_UPTIME = _("Uptime:")
TEXT_USERS_HEADER = _("Users (last active):")
TEXT_NO_USERS = _("No users online")
TEXT_AGO_SUFFIX = _("ago")
TEXT_LAST_UPDATED = _("Last updated at")

HEIGHT_BASE = 135
LINE_HEIGHT = 25
RADIUS = 12
ICON_SIZE = (16, 16)
PADDING_LEFT = 20
PADDING_TOP = 15
FONT_SIZES = {
    "title": 18,
    "normal": 14,
    "small": 13
}

ICON_CACHE = {
    "talking": Image.open(ICON_PATH_TALKING).resize(ICON_SIZE, Image.LANCZOS),
    "input_muted": Image.open(ICON_PATH_INPUT_MUTED).resize(ICON_SIZE, Image.LANCZOS),
    "output_muted": Image.open(ICON_PATH_OUTPUT_MUTED).resize(ICON_SIZE, Image.LANCZOS),
    "default": Image.open(ICON_PATH_DEFAULT).resize(ICON_SIZE, Image.LANCZOS),
}

def hex_to_rgb(hex_color) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def get_font(size) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_PATH, size)

def draw_rounded_rectangle(draw: ImageDraw.ImageDraw, xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)

def add_rounded_corners(img: Image.Image, radius) -> Image.Image:
    mask = Image.new('L', img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), img.size], radius=radius, fill=255)
    img.putalpha(mask)
    return img

def get_status_icon(client_flag_talking, client_input_muted, client_output_muted) -> Image.Image:
    if client_flag_talking:
        return ICON_CACHE["talking"]
    elif client_input_muted:
        return ICON_CACHE["input_muted"]
    elif client_output_muted:
        return ICON_CACHE["output_muted"]
    else:
        return ICON_CACHE["default"]

def get_activity_color(idle_time_ms: int, config: Config) -> str:
    idle_seconds = idle_time_ms // 1000
    if idle_seconds < config.max_active_seconds:
        return COLORS["text_secondary"]
    elif idle_seconds < config.max_away_seconds:
        return COLORS["yellow"]
    else:
        return COLORS["red"]

def draw_error(draw, errormsg, width, y_offset):
    font_title = get_font(FONT_SIZES["title"])
    font_normal = get_font(FONT_SIZES["normal"])
    draw.text((PADDING_LEFT, y_offset), TEXT_ERROR_TITLE,
              fill=hex_to_rgb(COLORS["red"]), font=font_title)
    y_offset += 35
    draw.text((PADDING_LEFT, y_offset), f"{TEXT_ERROR_PREFIX}{errormsg}",
              fill=hex_to_rgb(COLORS["text_secondary"]), font=font_normal)
    y_offset += 35
    return y_offset

def draw_header(draw, server_info, width, y_offset):
    font_title = get_font(FONT_SIZES["title"])
    font_normal = get_font(FONT_SIZES["normal"])

    draw.text((PADDING_LEFT, y_offset), server_info.name,
              fill=hex_to_rgb(COLORS["text_primary"]), font=font_title)

    y_offset += 35

    draw.text((PADDING_LEFT, y_offset), TEXT_USERS_ONLINE,
              fill=hex_to_rgb(COLORS["text_secondary"]), font=font_normal)

    users_count = f"{server_info.online_users_count}/{server_info.max_clients}"
    draw.text((150, y_offset), users_count,
              fill=hex_to_rgb(COLORS["text_primary"]), font=font_normal)

    uptime_x = width // 2 + 20
    draw.text((uptime_x + 20, y_offset), TEXT_UPTIME,
              fill=hex_to_rgb(COLORS["text_secondary"]), font=font_normal)

    uptime_value_x = uptime_x + 95
    draw.text((uptime_value_x, y_offset), server_info.uptime_formatted,
              fill=hex_to_rgb(COLORS["text_primary"]), font=font_normal)

    y_offset += LINE_HEIGHT
    return y_offset

def draw_users(draw, img, online_users, config, y_offset):
    font_normal = get_font(FONT_SIZES["normal"])
    font_small = get_font(FONT_SIZES["small"])

    draw.text((PADDING_LEFT, y_offset), TEXT_USERS_HEADER,
              fill=hex_to_rgb(COLORS["text_secondary"]), font=font_normal)
    y_offset += LINE_HEIGHT

    for user in online_users:
        status_icon = get_status_icon(
            user.flag_talking, user.input_muted, user.output_muted)

        img.paste(status_icon, (PADDING_LEFT, y_offset),
                  status_icon if status_icon.mode == 'RGBA' else None)

        username_x = PADDING_LEFT + 20
        draw.text((username_x, y_offset), user.nickname,
                  fill=hex_to_rgb(COLORS["text_primary"]), font=font_normal)

        idle_x = username_x + 180
        idle_text = f"({user.idle_time_formatted} {TEXT_AGO_SUFFIX})"
        idle_color = get_activity_color(user.idle_time, config)
        draw.text((idle_x, y_offset), idle_text, fill=hex_to_rgb(idle_color), font=font_small)
        y_offset += LINE_HEIGHT

    return y_offset

def draw_footer(draw, config, width, y_offset):
    font_normal = get_font(FONT_SIZES["normal"])
    timestamp = datetime.now(tz=ZoneInfo(config.timezone)).strftime('%H:%M:%S')
    draw.text((PADDING_LEFT, y_offset), f"{TEXT_LAST_UPDATED} {timestamp}", fill=hex_to_rgb(COLORS["text_secondary"]), font=font_normal)

def generate_status_image(server_info: ServerInfo, config: Config, width=450) -> io.BytesIO:
    base_height = HEIGHT_BASE
    if not server_info.has_error and server_info.online_users_count > 0:
        user_count = server_info.online_users_count
        user_list_height = max(user_count * LINE_HEIGHT, 30)
        height = base_height + user_list_height
    else:
        height = 110

    img = Image.new('RGBA', (width, height), hex_to_rgb(COLORS["card_bg"]) + (255,))
    draw = ImageDraw.Draw(img)

    y_offset = PADDING_TOP

    if server_info.has_error:
        y_offset = draw_error(draw, server_info.errormsg, width, y_offset)
    else:
        y_offset = draw_header(draw, server_info, width, y_offset)
        if server_info.online_users:
            y_offset = draw_users(draw, img, server_info.online_users, config, y_offset)
        y_offset += 10

    draw_footer(draw, config, width, y_offset)

    img = add_rounded_corners(img, radius=RADIUS)

    buffer = io.BytesIO()
    img.save(buffer, 'PNG', optimize=True)
    buffer.seek(0)
    return buffer
