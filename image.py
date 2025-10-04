from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io

from domain import ServerInfo

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

TEXT_ERROR_TITLE = "TeamSpeak Server Unavailable"
TEXT_ERROR_PREFIX = "Error: "
TEXT_USERS_ONLINE = "Users Online:"
TEXT_UPTIME = "Uptime:"
TEXT_USERS_HEADER = "Users (last active):"
TEXT_NO_USERS = "No users online"
TEXT_AGO_SUFFIX = "ago"
TEXT_LAST_UPDATED = "Last updated at"


def hex_to_rgb(hex_color) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def get_font(size) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_PATH, size)


def draw_rounded_rectangle(draw, xy, radius, fill, outline=None, width=1):
    x1, y1, x2, y2 = xy
    draw.rectangle([x1 + radius, y1, x2 - radius, y2],
                   fill=fill, outline=outline, width=width)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius],
                   fill=fill, outline=outline, width=width)


def add_rounded_corners(img, radius) -> Image.Image:
    mask = Image.new('L', img.size, 0)
    draw = ImageDraw.Draw(mask)

    draw.rounded_rectangle(
        [(0, 0), img.size],
        radius=radius,
        fill=255
    )

    img.putalpha(mask)
    return img



def get_status_icon(client_flag_talking, client_input_muted, client_output_muted) -> Image.Image:
    if client_flag_talking:
        ts_logo = Image.open(ICON_PATH_TALKING)
    elif client_input_muted:
        ts_logo = Image.open(ICON_PATH_INPUT_MUTED)
    elif client_output_muted:
        ts_logo = Image.open(ICON_PATH_OUTPUT_MUTED)
    else:
        ts_logo = Image.open(ICON_PATH_DEFAULT)

    ts_logo = ts_logo.resize((16, 16))
    return ts_logo


def generate_status_image(server_info: ServerInfo , width=450) -> io.BytesIO:
    font_title = get_font(18)
    font_normal = get_font(13)
    font_small = get_font(11)

    base_height = 135
    if not server_info.has_error and server_info.online_users_count > 0:
        user_count = server_info.online_users_count
        user_list_height = max(user_count * 25, 30)
        height = base_height + user_list_height
    else:
        height = 110

    img = Image.new('RGBA', (width, height), hex_to_rgb(
        COLORS["card_bg"]) + (255,))
    draw = ImageDraw.Draw(img)

    y_offset = 15

    if server_info.has_error:
        draw.text((20, y_offset), TEXT_ERROR_TITLE,
                  fill=hex_to_rgb(COLORS["red"]), font=font_title)
        y_offset += 35

        draw.text((20, y_offset), f"{TEXT_ERROR_PREFIX}{server_info.errormsg}",
                  fill=hex_to_rgb(COLORS["text_secondary"]), font=font_normal)
        
        y_offset += 35
    else:
        draw.text((20, y_offset), f"{server_info.name}",
                fill=hex_to_rgb(COLORS["text_primary"]), font=font_title)

        y_offset += 35

        draw.text((20, y_offset), TEXT_USERS_ONLINE,
                fill=hex_to_rgb(COLORS["text_secondary"]), font=font_normal)

        users_count = f"{server_info.online_users_count}/{server_info.max_clients}"
        draw.text((150, y_offset), users_count, fill=hex_to_rgb(
            COLORS["text_primary"]), font=font_normal)

        uptime_x = width // 2 + 20
        draw.text((uptime_x + 20, y_offset), TEXT_UPTIME,
                fill=hex_to_rgb(COLORS["text_secondary"]), font=font_normal)

        uptime_value_x = uptime_x + 95
        draw.text((uptime_value_x, y_offset), f"{server_info.uptime_formatted}",
                fill=hex_to_rgb(COLORS["text_primary"]), font=font_normal)

        if server_info.online_users:
            y_offset += 25
            draw.text((20, y_offset), TEXT_USERS_HEADER,
                    fill=hex_to_rgb(COLORS["text_secondary"]), font=font_normal)
            y_offset += 25

            for user in server_info.online_users:
                status_icon = get_status_icon(
                    user.flag_talking, user.input_muted, user.output_muted)

                circle_x = 0
                img.paste(status_icon, (circle_x + 20, y_offset),
                        status_icon if status_icon.mode == 'RGBA' else None)

                username_x = 40
                draw.text((username_x, y_offset), user.nickname,
                        fill=hex_to_rgb(COLORS["text_primary"]), font=font_normal)

                idle_x = username_x + 180
                draw.text((idle_x, y_offset), f"({user.idle_time_formatted} {TEXT_AGO_SUFFIX})",
                        fill=hex_to_rgb(COLORS["text_secondary"]), font=font_small)
                y_offset += 25
        else:
            y_offset += 25


        draw.text((20, y_offset), f"{TEXT_LAST_UPDATED} {datetime.now().strftime('%H:%M:%S')}",
                fill=hex_to_rgb(COLORS["text_secondary"]), font=font_normal)

    img = add_rounded_corners(img, radius=12)

    buffer = io.BytesIO()
    img.save(buffer, 'PNG', optimize=True)
    buffer.seek(0)
    return buffer
