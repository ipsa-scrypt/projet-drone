import speech_recognition as sr
import pyttsx3
import pyaudio
import keyboard

r = sr.Recognizer()
r.dynamic_energy_threshold = False

for index, name in enumerate(sr.Microphone.list_microphone_names()):
    print("Microphone with name \"{1}\" found for `Microphone(device_index={0})`".format(index, name))
def SpeakTest(command):
    engine=pyttsx3.init()
    engine.say(command)
    engine.runAndWait()


while True:
    print("test")
    if keyboard.read_key() == "d":
        print("Salut!")
        SpeakTest("le chat")

    if keyboard.read_key() == "alt gr":

        with sr.Microphone() as source2:
                # wait for a second to let the recognizer
                # adjust the energy threshold based on
                # the surrounding noise level
            print("Calibrated, now speak......")

            # listen for the use's imput
            audio2 = r.listen(source2, timeout=3)

            # Using google to recognise audio
            Mytext = r.recognize_google(audio2)
            Mytext = Mytext.lower()

            print("did you say : "+Mytext)
            SpeakTest(Mytext)
            break
def recup_command(text):
    if text == "take off":
        print("drone décolle")


recup_command(Mytext)
