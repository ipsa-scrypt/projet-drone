import olympe
import time
import olympe.messages.ardrone3.Piloting as piloting

DRONE_IP = "10.202.0.1" #ip du simu
DRONE_IP = "192.168.42.1" #ip du drone

time.sleep(5)
drone = olympe.Drone(DRONE_IP)
drone.connect()
assert drone(piloting.TakeOff()).wait().success()
time.sleep(5)
assert drone(piloting.Landing()).wait().success()
drone.disconnect()
