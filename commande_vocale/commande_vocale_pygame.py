import speech_recognition as sr
import pyttsx3
import keyboard
import olympe
import time
import olympe.messages.ardrone3.Piloting as piloting

r = sr.Recognizer()
r.dynamic_energy_threshold = False
DRONE_IP = "192.168.42.1" #ip du drone
drone = olympe.Drone(DRONE_IP)
drone.connect()

def check_devices():
    for index, name in enumerate(sr.Microphone.list_microphone_names()):
        print("Microphone with name \"{1}\" found for `Microphone(device_index={0})`".format(index, name))
        
    
def speaker(command):
    engine = pyttsx3.init()
    engine.say(command)
    engine.runAndWait()

running = True

def recup_command(text):
    if text == "take off":
        speaker("Le drone décolle")
        print("Le drone décolle")
        assert drone(piloting.TakeOff()).wait().success()
        
    elif text == "landing" or text == "lending" or text == "london":
        speaker("Le drone atterit")
        print("Le drone atterit")
        assert drone(piloting.Landing()).wait().success()
        
while running:
    if keyboard.read_key() == "d":
        speaker("le chat")

    if keyboard.read_key() == "alt gr":

        with sr.Microphone(device_index=1) as source2:
            r.energy_threshold = 2000
            print("> Speak now ......")
            audio2 = r.listen(source2, timeout=2)
            
            try :
                Mytext = r.recognize_google(audio2)
            except sr.UnknownValueError:
                print("Je n'ai pas compris ce que tu as dis, essaye de parler en anglais")
                
            Mytext = Mytext.lower()

            print("Tu as dis : " + Mytext)
            recup_command(Mytext)
