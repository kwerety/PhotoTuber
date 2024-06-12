import os
import subprocess
import sys
import pygame
import pyaudio
import numpy as np
import time

# Функция для установки библиотеки
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Установка необходимых библиотек
try:
    import pygame
except ImportError:
    install("pygame")
    import pygame

try:
    import pyaudio
except ImportError:
    install("pyaudio")
    import pyaudio

# Инициализация Pygame
pygame.init()

# Переменная для моргания
is_blinking = False

# Настройки окна
screen_width = 1280
screen_height = 720
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("PhotoTuber")

# Установка иконки окна и иконки в панели задач
icon_path = os.path.join(os.path.dirname(__file__), "pumpkin.png")
if os.path.exists(icon_path):
    icon = pygame.image.load(icon_path)
    pygame.display.set_icon(icon)
else:
    print(f"Иконка {icon_path} не найдена!")

# Загрузка изображений
images = {
    "normal": pygame.image.load("normal.png"),
    "loud": pygame.image.load("loud.png"),
    "very_loud": pygame.image.load("very_loud.png"),
    "blink_normal": pygame.image.load("blink_normal.png"),
    "blink_loud": pygame.image.load("blink_loud.png"),
    "blink_very_loud": pygame.image.load("blink_very_loud.png"),
}

# Установка начального выражения
current_image = images["normal"]

# Настройки текста
font = pygame.font.Font(None, 36)
instructions_text = font.render("Press 'h' to hide text. Use 'ws' and 'ad' to adjust thresholds.", True, (255, 255, 255))

# Инициализация PyAudio
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

p = pyaudio.PyAudio()

# Список микрофонов
device_count = p.get_device_count()
input_devices = [p.get_device_info_by_index(i) for i in range(device_count) if p.get_device_info_by_index(i)['maxInputChannels'] > 0]

def select_microphone():
    selected_device_index = 0

    while True:
        screen.fill((0, 0, 0))  # Черный фон
        title_text = font.render("Select Input Device (use 'w'/'s' and Enter):", True, (255, 255, 255))
        screen.blit(title_text, (10, 10))

        for i, device in enumerate(input_devices):
            color = (255, 255, 255) if i == selected_device_index else (100, 100, 100)
            device_text = font.render(f"{i}: {device['name']}", True, color)
            screen.blit(device_text, (10, 50 + i * 40))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w:
                    selected_device_index = (selected_device_index - 1) % len(input_devices)
                elif event.key == pygame.K_s:
                    selected_device_index = (selected_device_index + 1) % len(input_devices)
                elif event.key == pygame.K_RETURN:
                    return input_devices[selected_device_index]['index']

selected_device = select_microphone()

stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                input_device_index=selected_device,
                frames_per_buffer=CHUNK)

def get_volume():
    data = np.frombuffer(stream.read(CHUNK, exception_on_overflow=False), dtype=np.int16)
    volume = np.linalg.norm(data) / np.sqrt(len(data))
    return volume

# Настройки моргания
blink_interval = 5  # интервал между морганиями в секундах
blink_duration = 0.1  # продолжительность моргания в секундах
last_blink_time = time.time()  # время последнего моргания
blink_start_time = 0  # время начала текущего моргания

# Пороговые значения для громкости
THRESHOLDS = {
    'normal': 300,
    'loud': 1000
}

# Основной цикл программы
running = True
show_text = True  # Переменная для отображения текста

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_h:  # Нажатие на клавишу "h" для переключения видимости текста
                show_text = not show_text
            elif event.key == pygame.K_w:  # Увеличение порога normal
                THRESHOLDS['normal'] += 50
            elif event.key == pygame.K_s:  # Уменьшение порога normal
                THRESHOLDS['normal'] = max(0, THRESHOLDS['normal'] - 50)
            elif event.key == pygame.K_a:  # Увеличение порога loud
                THRESHOLDS['loud'] += 50
            elif event.key == pygame.K_d:  # Уменьшение порога loud
                THRESHOLDS['loud'] = max(0, THRESHOLDS['loud'] - 50)

    # Получение громкости микрофона
    volume = get_volume()

    # Проверка, не пора ли моргать
    current_time = time.time()
    if not is_blinking and (current_time - last_blink_time >= blink_interval):
        is_blinking = True
        last_blink_time = current_time
        blink_start_time = current_time

    # Если моргаем, выбираем соответствующее изображение моргания
    if is_blinking:
        if current_time - blink_start_time < blink_duration:
            current_image = images[f"blink_{'very_loud' if volume >= THRESHOLDS['loud'] else 'loud' if volume >= THRESHOLDS['normal'] else 'normal'}"]
        else:
            is_blinking = False

    # Если не моргаем, выбираем обычное изображение
    if not is_blinking:
        current_image = images['very_loud' if volume >= THRESHOLDS['loud'] else 'loud' if volume >= THRESHOLDS['normal'] else 'normal']

    # Отображение изображения на экране с зеленым фоном
    screen.fill((0, 255, 0))  # Зеленый фон
    
    # Центрирование изображения
    img_rect = current_image.get_rect(center=(screen_width // 2, screen_height // 2))
    screen.blit(current_image, img_rect.topleft)

    # Отображение текста, если не скрыт
    if show_text:
        screen.blit(instructions_text, (10, 10))
        volume_text = font.render(f"Volume: {int(volume)}", True, (255, 255, 255))
        screen.blit(volume_text, (10, 50))
        threshold_text = font.render(f"Thresholds: Normal: {THRESHOLDS['normal']}, Loud: {THRESHOLDS['loud']}", True, (255, 255, 255))
        screen.blit(threshold_text, (10, 90))

    pygame.display.flip()

# Завершение PyAudio и Pygame
stream.stop_stream()
stream.close()
p.terminate()
pygame.quit()
sys.exit()
