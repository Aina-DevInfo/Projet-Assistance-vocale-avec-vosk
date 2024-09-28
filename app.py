#!/usr/bin/env python3

# prerequisites: as described in https://alphacephei.com/vosk/install and also python module `sounddevice` (simply run command `pip install sounddevice`)
# Example usage using Dutch (nl) recognition model: `python test_microphone.py -m nl`
# For more help run: `python test_microphone.py -h`

import argparse
import datetime
import json
import os
import queue
import sys
import time
import sounddevice as sd # type: ignore

from vosk import Model, KaldiRecognizer

q = queue.Queue()


def speek(mot):
    import pyttsx3
    text_speech = pyttsx3.init()
    text_speech.say(mot)
    text_speech.runAndWait() 

def welcome():
    hour = datetime.datetime.now().hour
    if hour >= 3 and hour < 12:
        speek('Bonjour monsieur, que puis-je vous aider')
    if hour >= 12 and hour < 18:
        speek('bonne après midi monsieur, que puis-je vous aider')
    if hour >= 18 and hour < 21:
        speek('Bonsoir monsieur, que puis-je vous aider')

# controle de volume
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL

devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_,CLSCTX_ALL,None)
volume = cast(interface, POINTER(IAudioEndpointVolume))

def set_volume(percentage):
    volume_level = min(max(percentage/100.0,0.0),1.0)    
    volume.SetMasterVolumeLevelScalar(volume_level,None)


def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text

def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument(
    "-l", "--list-devices", action="store_true",
    help="show list of audio devices and exit")
args, remaining = parser.parse_known_args()
if args.list_devices:
    print(sd.query_devices())
    parser.exit(0)
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[parser])
parser.add_argument(
    "-f", "--filename", type=str, metavar="FILENAME",
    help="audio file to store recording to")
parser.add_argument(
    "-d", "--device", type=int_or_str,
    help="input device (numeric ID or substring)")
parser.add_argument(
    "-r", "--samplerate", type=int, help="sampling rate")
parser.add_argument(
    "-m", "--model", type=str, help="language model; e.g. en-us, fr, nl; default is en-us")
args = parser.parse_args(remaining)

try:
    if args.samplerate is None:
        device_info = sd.query_devices(args.device, "input")
        # soundfile expects an int, sounddevice provides a float:
        args.samplerate = int(device_info["default_samplerate"])
        
    if args.model is None:
        #model = Model(lang="en-us")
        model = Model(lang="fr")
    else:
        model = Model(lang=args.model)

    if args.filename:
        dump_fn = open(args.filename, "wb")
    else:
        dump_fn = None

    with sd.RawInputStream(samplerate=args.samplerate, blocksize = 8000, device=args.device,
            dtype="int16", channels=1, callback=callback):
        print("#" * 80)
        print("Press Ctrl+C to stop the recording")
        print("#" * 80)

        rec = KaldiRecognizer(model, args.samplerate)
        while True:
            nouveau_volume = int(volume.GetMasterVolumeLevelScalar()*100)
            etat_L1 =  True
            etat_L2 = True
            etat_Port = True
            data = q.get()
            if rec.AcceptWaveform(data):
                parle = json.loads(rec.FinalResult())
                print(parle['text'])
                #print(rec.FinalResult)
                
                if 'bonjour emma' in parle['text']:
                    welcome()
                if 'emma ouvrez la porte'  in parle['text']:
                    speek('Oui monsieur, la porte va ouvrir après quelque seconde, vous voudriez autre chose ?')
                if 'emma fermer la porte'  in parle['text'] :
                    etat_Port = False
                    speek('Oui monsieur, la porte va fermer après quelque seconde, vous voudriez autre chose ?')
                if 'emma éteignez la lampe numéro un' in parle['text']:
                    speek("Oui monsieur, la lumière numéro un va s'éteindre après quelque seconde, vous voudriez autre chose ?")
                if 'emma allumer la lampe numéro un' in parle['text']:
                    speek("Oui monsieur, la lumière numéro un va s'allumer après quelque seconde, vous voudriez autre chose ?")
                if 'emma éteignez la lampe numéro deux' in parle['text']:
                    speek("Oui monsieur, la lumière numéro deux va s'éteindre après quelque seconde, vous voudriez autre chose ?")
                if 'emma allumer la lampe numéro deux' in parle['text']:
                    speek("Oui monsieur, la lumière numéro deux va s'allumer après quelque seconde, vous voudriez autre chose ?")
                if 'quelle heure' in parle ['text']:
                    Time = datetime.datetime.now().strftime('%H heure:%M')
                    speek("il est "+ Time)
                if 'lance la musique' in parle ['text']:
                    speek("voilà un chonson plus romantique, amuser vous bien")
                    os.startfile('Fitia sahala.mp3')
                if 'arrêté le système' in parle['text']:
                    speek("le système va s'arrêté après 5 seconde")
                    time.sleep(5)
                    parser.exit(0)
                if 'éteignez la musique' in parle ['text']:
                    # import subprocess
                    # subprocess.run("taskkill","/IM", "PotPlayerMini64.exe","/F")

                    import signal
                    for line in os.popen("tasklist"):
                        if "PotPlayerMini64.exe" in line :
                            pid = int(line.split()[1])
                            os.kill(pid, signal.SIGTERM)
                    speek("la musique est éteindre, est ce qu'il y a d'autre chose que je puis vous aidé ?")
                if 'augmente le volume' in parle ['text']:
                    if int(nouveau_volume) == 100 :
                        speek("le volume est déjà 100 %")
                        continue
                    set_volume(int(nouveau_volume)+10)
                    print(int(nouveau_volume))
                    speek("volume augmenter "+str(int(nouveau_volume))+" %")
                if 'baissez le volume' in parle ['text']:
                    set_volume(int(nouveau_volume)-10)
                    if int(nouveau_volume) == 0 :
                        speek("le volume est déjà 0 %")
                        continue
                    speek("volume diminue "+str(int(nouveau_volume))+" %")

            if dump_fn is not None:
                dump_fn.write(data)
            


except KeyboardInterrupt:
    print("\nDone")
    parser.exit(0)
except Exception as e:
    parser.exit(type(e).__name__ + ": " + str(e))