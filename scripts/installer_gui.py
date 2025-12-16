#!/usr/bin/env python3
import os
import sys
import time
import subprocess
import threading
import pygame
from pathlib import Path

# --- CONFIGURAZIONE SISTEMA ---
# 1. VIDEO: Usa KMSDRM (Accelerazione Hardware senza X11)
os.environ["SDL_VIDEODRIVER"] = "kmsdrm"

# 2. INPUT: Configurazione specifica per Touchscreen QDTECH
os.environ["SDL_MOUSEDRV"] = "evdev"
os.environ["SDL_MOUSEDEV"] = "/dev/input/event0"
os.environ["SDL_MOUSE_RELATIVE"] = "0"

# Recupero variabili utente
SUDO_USER = os.environ.get('SUDO_USER', 'pi')
try:
    import pwd
    pw_record = pwd.getpwnam(SUDO_USER)
    USER_HOME = pw_record.pw_dir
    USER_UID = pw_record.pw_uid
    USER_GID = pw_record.pw_gid
except KeyError:
    print(f"Utente {SUDO_USER} non trovato!")
    sys.exit(1)

PROJECT_DIR = os.path.join(USER_HOME, "rpi_car_infotainment")
LOG_FILE = "/var/log/rpi_car_installer.log"

# --- COLORI & UI ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_GRAY = (30, 30, 30)
BLUE = (0, 120, 215)
GREEN = (0, 200, 100)
RED = (220, 50, 50)

# --- FUNZIONI HELPER ---
def run_cmd(command, as_user=None):
    cmd_str = command
    if isinstance(command, list):
        cmd_str = " ".join(command)
    
    prefix = ""
    if as_user:
        final_cmd = [f"sudo -u {as_user} bash -c '{cmd_str}'"]
        shell_mode = True
    else:
        final_cmd = command
        shell_mode = isinstance(command, str)

    with open(LOG_FILE, "a") as log:
        log.write(f"\n>>> EXEC: {cmd_str}\n")
        try:
            subprocess.run(final_cmd, shell=shell_mode, check=True, stdout=log, stderr=log)
        except subprocess.CalledProcessError as e:
            log.write(f"!!! ERROR: {e}\n")
            raise e

def write_file(path, content):
    with open(path, "w") as f:
        f.write(content)

# --- STEP DI INSTALLAZIONE (Placeholder logica reale) ---
# Qui incollerai le tue funzioni step_update_system, step_config_boot, ecc.
# Per brevità lascio solo lo scheletro funzionante per la GUI.

def step_update_system():
    run_cmd("apt update")
    # Aggiungi qui apt upgrade se vuoi
    time.sleep(2) # Simulazione

def step_config_boot():
    time.sleep(1) # Simulazione

def step_setup_bluetooth():
    time.sleep(1) # Simulazione

def step_python_env():
    time.sleep(2) # Simulazione

def step_audio_setup():
    time.sleep(1) # Simulazione

def step_install_service():
    time.sleep(1) # Simulazione

# Lista step
INSTALL_STEPS = [
    ("Update OS", step_update_system),
    ("Boot Config", step_config_boot),
    ("Bluetooth", step_setup_bluetooth),
    ("Python Env", step_python_env),
    ("Audio", step_audio_setup),
    ("Service", step_install_service),
]

# --- THREAD INSTALLAZIONE ---
class InstallThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.progress = 0
        self.current_step = ""
        self.done = False
        self.error = None

    def run(self):
        total = len(INSTALL_STEPS)
        try:
            for i, (name, func) in enumerate(INSTALL_STEPS):
                self.current_step = name
                self.progress = int((i / total) * 100)
                func()
            self.progress = 100
            self.current_step = "Completato!"
            self.done = True
        except Exception as e:
            self.error = str(e)

def draw_text_centered(surface, text, font, color, rect):
    text_surf = font.render(text, True, color)
    text_rect = text_surf.get_rect(center=rect.center)
    surface.blit(text_surf, text_rect)

# --- MAIN GUI ---
def main():
    pygame.init()
    
    # 1024x600 Risoluzione Nativa
    W, H = 1024, 600
    print(f"!!! DEBUG: Avvio {W}x{H} KMSDRM + EVDEV !!!")
    
    # Setup Schermo
    screen = pygame.display.set_mode((W, H), pygame.FULLSCREEN | pygame.DOUBLEBUF)
    pygame.mouse.set_visible(True) # Utile per debug, puoi metterlo False dopo

    # Font: Usa None per evitare crash se mancano i font di sistema
    font_large = pygame.font.Font(None, 60)
    font_med = pygame.font.Font(None, 40)
    font_small = pygame.font.Font(None, 25)

    running = True
    installing = False
    worker = None
    
    # Pulsanti
    btn_start = pygame.Rect(W//2 - 150, H//2 - 50, 300, 100)
    btn_exit = pygame.Rect(W - 120, 20, 100, 50)
    
    clock = pygame.time.Clock()

    while running:
        screen.fill(DARK_GRAY)
        
        events = pygame.event.get()
        for event in events:
            # Uscita
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            
            # --- GESTIONE INPUT UNIFICATA (MOUSE + TOUCH) ---
            click_pos = None
            
            # Caso A: Mouse Click
            if event.type == pygame.MOUSEBUTTONDOWN:
                click_pos = event.pos
                print(f"DEBUG: Mouse Click {click_pos}")

            # Caso B: Finger Touch (Fondamentale per il tuo schermo)
            elif event.type == pygame.FINGERDOWN:
                # Converte 0.0-1.0 in pixel reali
                x = int(event.x * W)
                y = int(event.y * H)
                click_pos = (x, y)
                print(f"DEBUG: Touch {click_pos}")

            # --- LOGICA CLICK ---
            if click_pos:
                if not installing:
                    # Start
                    if btn_start.collidepoint(click_pos):
                        installing = True
                        worker = InstallThread()
                        worker.start()
                    # Exit
                    if btn_exit.collidepoint(click_pos):
                        running = False
                elif installing and worker and worker.done:
                    # Reboot
                    if btn_start.collidepoint(click_pos):
                         subprocess.run(["reboot"])

        # --- DISEGNO ---
        title = font_large.render("RPi Installer Infotainment", True, WHITE)
        screen.blit(title, (50, 50))

        if installing:
            status_text = f"Step: {worker.current_step}"
            if worker.error:
                 status_text = f"ERRORE: {worker.error}"
                 col = RED
            else:
                 col = BLUE
            
            # Barra
            pygame.draw.rect(screen, BLACK, (50, H//2 - 20, W-100, 40))
            fill_w = (W-100) * (worker.progress / 100.0)
            pygame.draw.rect(screen, col, (50, H//2 - 20, fill_w, 40))
            
            lbl = font_med.render(f"{worker.progress}% - {status_text}", True, WHITE)
            screen.blit(lbl, (50, H//2 + 30))
            
            if worker.done:
                pygame.draw.rect(screen, GREEN, btn_start, border_radius=15)
                draw_text_centered(screen, "RIAVVIA ORA", font_med, WHITE, btn_start)
            elif worker.error:
                pygame.draw.rect(screen, RED, btn_start, border_radius=15)
                draw_text_centered(screen, "ERRORE", font_med, WHITE, btn_start)

        else:
            pygame.draw.rect(screen, BLUE, btn_start, border_radius=15)
            draw_text_centered(screen, "INSTALLA", font_large, WHITE, btn_start)
            
            info = font_small.render("Richiede connessione Internet attiva.", True, WHITE)
            screen.blit(info, (W//2 - 150, H//2 + 70))

        pygame.draw.rect(screen, RED, btn_exit, border_radius=5)
        draw_text_centered(screen, "ESCI", font_small, WHITE, btn_exit)

        pygame.display.flip()
        clock.tick(30) # 30 FPS bastano

    pygame.quit()

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("Devi essere root!")
    else:
        main()