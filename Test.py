import usrtFaceTracking as ft
import servoControllerAltUSB as sc
import queue
import threading
import time

# (Pixels)
CAMERA_WIDTH = 320
# (Pixels)
CAMERA_HEIGHT = 240
# (Frames per second)
CAMERA_FPS = 8
# (N)
CAMERA_INDEX = 0
# (File containing cascade classifier)
CASCADE_CLASSIFIER = 'haarcascade_frontalface_alt.xml'
# (multiplier greater than 1)
SCALE_FACTOR = 1.2
# (N)
MIN_NEIGHBORS = 2
# (Pixels, Pixels)
MIN_SIZE = (1, 1)
# (Multiplier)
MOTION_TOLERANCE = 0.75
# (Seconds)
TRACKING_GRACE = 0.5
# (Number of frames)
ROLLING_AVG_COUNT = 5
# (Pixels)
CENTER_WIDTH = 15
# (N)
SERVO_PIN = 12
# (Pulse width ms)
SERVO_MIN = 0.5
# (Pulse width ms)
SERVO_MAX = 2.5
# (Degrees per second)
SPEED = 30
# (Boolean)
REVERSE = True

fifoQueue = queue.Queue()

def servo_thread(servo):
    while True:
        try:
            status = fifoQueue.get(block=False)
            if status == 0:
                break
            servo.updateStatus(status)
        except queue.Empty:
            pass
        
        servo.runServoLoop()
        time.sleep(0.02)

def main():
    
    servo1 = sc.ServoController(SERVO_PIN, SERVO_MIN, SERVO_MAX, SPEED, REVERSE)
    t_servo = threading.Thread(target=servo_thread, args =(servo1,))
    t_servo.start()
    while True:
        status = int(input("Please enter status: "))
        fifoQueue.put(status)
        if status == 0:
            break
            
    t_servo.join()

if __name__ == "__main__":
    main()