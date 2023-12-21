import speech_recognition as sr
import pyttsx3
import keyboard

r = sr.Recognizer()
r.dynamic_energy_threshold = False

def check_devices():
    for index, name in enumerate(sr.Microphone.list_microphone_names()):
        print("Microphone with name \"{1}\" found for `Microphone(device_index={0})`".format(index, name))
    
def speaker(command):
    engine = pyttsx3.init()
    engine.say(command)
    engine.runAndWait()

running = True

while running:
    if keyboard.read_key() == "d":
        speaker("le chat")

    if keyboard.read_key() == "alt gr":

        with sr.Microphone() as source2:
            print("> Speak now ......")
            audio2 = r.listen(source2, timeout=3)
            
            try :
                Mytext = r.recognize_google(audio2)
            except sr.UnknownValueError:
                print("Je n'ai pas compris ce que tu as dis, essaye de parler en anglais")
                
            Mytext = Mytext.lower()

            print("Tu as dis : " + Mytext)
            break
        
def recup_command(text):
    if text == "take off":
        speaker("Le drone décolle")
        print("Le drone décolle")

#check_devices()
recup_command(Mytext)
