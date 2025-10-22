import serial
import time


class ServoController:
    def __init__(self, servo_pin, minMs, maxMs, speed, reverse):

        try:
            self.ser = serial.Serial('/dev/cu.usbmodem11301', 115200, timeout=0.1)
            time.sleep(2)
        except serial.SerialException as e:
            self.ser = None
            return

        self.pin = servo_pin
        self.minDuty = (minMs * 100) / 20
        self.maxDuty = (maxMs * 100) / 20
        self.speed = (speed / 180) * (self.maxDuty - self.minDuty)
        self.currentDuty = self.minDuty + (self.maxDuty - self.minDuty) / 2
        self.status = 1
        self.reversed = 1 if reverse else 0
        self.frequency = 50

        
    
    def __del__(self):
        if hasattr(self, 'ser') and self.ser is not None:
            self.ser.close()

    def updateStatus(self, status):
        self.status = status
    
    def runServoLoop(self):
        if self.status == 1:
            targetDuty = self.minDuty + (self.maxDuty - self.minDuty) / 2
            if abs(self.currentDuty - targetDuty) > self.speed * 0.02:
                if self.currentDuty > targetDuty:
                    self.currentDuty -= self.speed * 0.02
                else:
                    self.currentDuty += self.speed * 0.02
            else:
                self.currentDuty = targetDuty
        elif self.status == 3 + self.reversed:
            if (self.currentDuty - self.speed * 0.02 > self.minDuty):
                self.currentDuty -= self.speed * 0.02
            else:
                self.currentDuty = self.minDuty
        elif self.status == 4 - self.reversed:
            if (self.currentDuty + self.speed * 0.02 < self.maxDuty):
                self.currentDuty += self.speed * 0.02
            else:
                self.currentDuty = self.maxDuty

        command = f"{int(round(self.currentDuty * 10000))}\n"
        #print(command)
        if self.ser is None:
            return
        try:
            #print("Sending" + str(command.encode('ascii')))
            self.ser.write(command.encode('ascii'))
        except serial.SerialException as e:
            print(f"Error writing to serial port: {e}")
            self.ser = None
        #print((self.currentDuty - self.minDuty) / (self.maxDuty - self.minDuty) * 180)
