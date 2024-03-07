import speech_recognition as sr
import pyttsx3
import pyaudio
import keyboard

r = sr.Recognizer()

def SpeakTest(command):
    engine=pyttsx3.init()
    engine.say(command)
    engine.runAndWait()


while True:
    if keyboard.read_key() == "d":
        print("Salut!")
        SpeakTest("le chat")

    if keyboard.read_key() == "alt gr":

        with sr.Microphone() as source2:
                # wait for a second to let the recognizer
                # adjust the energy threshold based on
                # the surrounding noise level
            print("Silence please, calibratiing background noise")
            r.adjust_for_ambient_noise(source2, duration=2)
            print("Calibrated, now speak......")

            # listen for the use's imput
            audio2 = r.listen(source2)

            # Using google to recognise audio
            Mytext = r.recognize_google(audio2)
            Mytext = Mytext.lower()

            print("did you say : "+Mytext)
            SpeakTest(Mytext)
