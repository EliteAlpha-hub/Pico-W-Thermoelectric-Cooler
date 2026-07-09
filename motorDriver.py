from machine import PWM,Pin

class Motor:
        def __init__(self, enable_pin, p, n):
            self.enable_pin = enable_pin
            self.p = p
            self.n = n
            
            en = Pin(self.enable_pin, Pin.OUT)
            self.en_pwm = PWM(en)
            self.p1 = Pin(self.p, Pin.OUT)
            self.p2 = Pin(self.n, Pin.OUT)
            self.en_pwm.duty_u16(0)
            
        def start(self, direction=1):
            self.en_pwm.deinit()  
            en = Pin(self.enable_pin, Pin.OUT)
            en.on()
            if direction > 0:
                self.p1.high()
                self.p2.low()
            else:
                self.p1.low()
                self.p2.high()
            
        def stop(self):
            self.p1.low()
            self.p2.low()
            self.en_pwm.duty_u16(0)
        
        def pwm_start(self, percent, direction=1):
            duty = int(percent * 65535 / 100)
            self.en_pwm.freq(1000)
            self.en_pwm.duty_u16(duty)
            if direction > 0:
                self.p1.high()
                self.p2.low()
            else:
                self.p1.low()
                self.p2.high()