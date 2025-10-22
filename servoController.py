from rpi_hardware_pwm import HardwarePWM


class ServoController:
    def __init__(self, servo_pin, minMs, maxMs, speed, reverse):
        self.pin = servo_pin
        self.minDuty = (minMs * 100) / 20
        self.maxDuty = (maxMs * 100) / 20
        self.speed = (speed / 180) * (self.maxDuty - self.minDuty)
        self.currentDuty = self.minDuty + (self.maxDuty - self.minDuty) / 2
        self.status = 1
        self.reversed = 1 if reverse else 0
        self.frequency = 50

        self.pwm = HardwarePWM(pwm_channel=2, hz=self.frequency, chip=0)
        self.pwm.start(self.currentDuty)
    
    def __del__(self):
        self.pwm.stop()

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
        self.pwm.change_duty_cycle(self.currentDuty)
        #print((self.currentDuty - self.minDuty) / (self.maxDuty - self.minDuty) * 180)
