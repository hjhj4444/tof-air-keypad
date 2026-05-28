import pygame
import serial
import sys
import time

COM_PORT = "COM6"
BAUD = 115200

pygame.init()

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()
pygame.display.set_caption("ToF Keypad UI")
clock = pygame.time.Clock()

KEY_FONT = pygame.font.SysFont("arial", int(HEIGHT * 0.045), bold=True)
LABEL_FONT = pygame.font.SysFont("malgungothic", int(HEIGHT * 0.024), bold=True)
VALUE_FONT = pygame.font.SysFont("consolas", int(HEIGHT * 0.040), bold=True)
STATUS_FONT = pygame.font.SysFont("malgungothic", int(HEIGHT * 0.030), bold=True)

BG = (8, 12, 18)
PANEL = (20, 28, 40)
KEY_NORMAL = (55, 65, 82)
KEY_FLASH = (130, 170, 255)
KEY_TEXT = (245, 247, 250)
BORDER = (130, 145, 170)
BORDER_HIGHLIGHT = (255, 255, 255)
WHITE = (255, 255, 255)
SOFT = (180, 190, 205)
CANCEL_COLOR = (170, 80, 80)
OK_COLOR = (70, 150, 100)

keys = [
    ["1", "2", "3"],
    ["4", "5", "6"],
    ["7", "8", "9"],
    ["CANCEL", "0", "OK"]
]

highlight = None
flash_key = None
flash_until = 0.0
input_buffer = []
status_text = "READY"

grid_w = int(WIDTH * 0.40)
grid_h = int(HEIGHT * 0.55)
gap = int(min(WIDTH, HEIGHT) * 0.018)

cell_w = (grid_w - gap * 2) // 3
cell_h = (grid_h - gap * 3) // 4

grid_x = int(WIDTH * 0.22)
grid_y = (HEIGHT - grid_h) // 2

input_w = int(WIDTH * 0.20)
input_h = int(HEIGHT * 0.12)
input_x = WIDTH - input_w - int(WIDTH * 0.05)
input_y = int(HEIGHT * 0.12)

status_w = int(WIDTH * 0.20)
status_h = int(HEIGHT * 0.12)
status_x = WIDTH - status_w - int(WIDTH * 0.05)
status_y = HEIGHT - status_h - int(HEIGHT * 0.12)

input_rect = pygame.Rect(input_x, input_y, input_w, input_h)
status_rect = pygame.Rect(status_x, status_y, status_w, status_h)


def draw_text(text, font, color, x, y, center=False):
    surf = font.render(text, True, color)
    rect = surf.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(surf, rect)


def get_key_rect(r, c):
    x = grid_x + c * (cell_w + gap)
    y = grid_y + r * (cell_h + gap)
    return pygame.Rect(x, y, cell_w, cell_h)


def handle_protocol_line(line: str):
    global highlight, flash_key, flash_until, status_text, input_buffer

    if line.startswith("HIGHLIGHT:"):
        value = line.split(":", 1)[1].strip()
        if value == "NONE":
            highlight = None
        else:
            highlight = value

    elif line.startswith("CONFIRM:"):
        value = line.split(":", 1)[1].strip()

        flash_key = value
        flash_until = time.time() + 0.20

        if value.isdigit():
            if len(input_buffer) < 4:
                input_buffer.append(value)
        elif value == "CANCEL":
            input_buffer.clear()
        elif value == "OK":
            pass

    elif line.startswith("MSG:"):
        value = line.split(":", 1)[1].strip()
        status_text = value

        if value in ("CLEARED", "WRONG", "OK"):
            input_buffer.clear()


def draw_keypad():
    now = time.time()

    for r in range(4):
        for c in range(3):
            label = keys[r][c]
            rect = get_key_rect(r, c)

            if label == "CANCEL":
                base = CANCEL_COLOR
            elif label == "OK":
                base = OK_COLOR
            else:
                base = KEY_NORMAL

            is_flash = (label == flash_key) and (now < flash_until)
            is_highlight = (label == highlight)

            fill = KEY_FLASH if is_flash else base
            border = BORDER_HIGHLIGHT if is_highlight else BORDER
            border_width = 4 if is_highlight else 2

            pygame.draw.rect(screen, fill, rect, border_radius=18)
            pygame.draw.rect(screen, border, rect, border_width, border_radius=18)

            draw_text(label, KEY_FONT, KEY_TEXT, rect.centerx, rect.centery, center=True)


def draw_input_panel():
    pygame.draw.rect(screen, PANEL, input_rect, border_radius=18)
    pygame.draw.rect(screen, (55, 70, 95), input_rect, 2, border_radius=18)

    padded = input_buffer[:]
    while len(padded) < 4:
        padded.append("_")
    input_str = "  ".join(padded)

    draw_text("INPUT", LABEL_FONT, SOFT, input_rect.x + 20, input_rect.y + 14)
    draw_text(input_str, VALUE_FONT, WHITE, input_rect.x + 20, input_rect.y + input_rect.h // 2 + 4)


def draw_status_panel():
    pygame.draw.rect(screen, PANEL, status_rect, border_radius=18)
    pygame.draw.rect(screen, (55, 70, 95), status_rect, 2, border_radius=18)

    draw_text("STATUS", LABEL_FONT, SOFT, status_rect.x + 20, status_rect.y + 14)
    draw_text(status_text, STATUS_FONT, WHITE, status_rect.x + 20, status_rect.y + status_rect.h // 2 + 8)


def try_open_serial():
    try:
        ser = serial.Serial(COM_PORT, BAUD, timeout=0.01)
        print("serial opened")
        return ser
    except Exception as e:
        print("serial open failed:", e)
        return None


ser = try_open_serial()
line_buffer = ""

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            if ser:
                ser.close()
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if ser:
                    ser.close()
                pygame.quit()
                sys.exit()

    if ser:
        try:
            while ser.in_waiting > 0:
                ch = ser.read(1).decode(errors="ignore")
                if ch == "\n":
                    line = line_buffer.strip()
                    line_buffer = ""
                    if line:
                        print("받음:", line)
                        handle_protocol_line(line)
                elif ch != "\r":
                    line_buffer += ch
        except Exception as e:
            status_text = f"SERIAL ERROR: {e}"

    screen.fill(BG)
    draw_keypad()
    draw_input_panel()
    draw_status_panel()
    pygame.display.flip()
    clock.tick(60)
