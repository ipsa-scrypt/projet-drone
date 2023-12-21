import speech_recognition as sr
import pyttsx3
import pygame
import sys
pygame.init()

r = sr.Recognizer()
r.dynamic_energy_threshold = True

def check_devices():
    for index, name in enumerate(sr.Microphone.list_microphone_names()):
        print("Microphone with name \"{1}\" found for `Microphone(device_index={0})`".format(index, name))

def speaker(command):
    engine = pyttsx3.init()
    engine.say(command)
    engine.runAndWait()
                
def recup_command(Mytext):
    if Mytext == "take off":
        speaker("Le drone décolle")
        #assert drone(piloting.TakeOff()).wait().success()
        print("Le drone décolle")

running = True

screen = pygame.display.set_mode((500, 500))

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            print("1")
            if event.key == pygame.K_d:
                speaker("le chat")
            

            if event.key== pygame.K_p:
                with sr.Microphone() as source2:
                    print("> Speak now ......")
                    audio2 = r.listen(source2, timeout = 3, phrase_time_limit = 3)
                    
                    try :
                        Mytext = r.recognize_google(audio2)
                        ytext = Mytext.lower()
                        print("Tu as dis : " + Mytext)
                        recup_command(Mytext)
                        break
                    except sr.UnknownValueError:
                        print("Je n'ai pas compris ce que tu as dis, essaye de parler en anglais")

    pygame.display.flip()

#check_devices()
pygame.quit()
    
