import winsound
import threading
import os
import time

siren_playing = False

def play_sound():
    path = os.path.join(os.path.dirname(__file__), "siren.wav")
    winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)

def play_siren():
    global siren_playing
    if not siren_playing:
        siren_playing = True
        threading.Thread(target=play_sound).start()

play_siren()
time.sleep(2)