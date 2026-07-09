 Core 0: Main program (Temperature sensing, motor control, OLED display)
# Core 1: Web server
import _thread,json,onewire,ds18x20,time,network,math,socket
from machine import Pin, SoftI2C, PWM, ADC, reset
import secrets,motorDriver,webpage,ssd1306


# Constants
OLED_WIDTH = 128
OLED_HEIGHT = 32
MODE_OFF = 0
MODE_ZIP = 1  # Lowest cooling (24°C)
MODE_ZAP = 2  # Medium cooling (18°C)
MODE_ZOOM = 3  # Max cooling
MODE_NAMES = ["OFF", "ZIP", "ZAP", "ZOOM"]
TARGET_TEMPS = [0, 20, 10, -100]  # Target temps for each mode

# Global variables
temp1C = 0.0
temp2C = 0.0
current_mode = 3
fan_speed = 0
peltier_power = 0
web_clients = []
last_display_update = 0

def toggle_mode():
    global current_mode,MODE_NAMES
    if current_mode == 3:
        current_mode = 0
    else:
        current_mode += 1
    oled.progress_bar(MODE_NAMES[current_mode])

# Hardware setup
def setup_hardware():
    global i2c, oled, led, ds_pin1, ds_pin2, ds_sensor1, ds_sensor2, roms1, roms2, fan, peltier,button
    
    # OLED setup
    i2c = SoftI2C(scl=Pin(17), sda=Pin(16))
    oled = ssd1306.SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, i2c)

    #Button setup
    button = Pin(2,Pin.IN,Pin.PULL_DOWN)

    # LED setup
    led = Pin("LED", Pin.OUT)
    
    # Temperature sensors setup
    ds_pin1 = Pin(15)
    ds_pin2 = Pin(14)
    ds_sensor1 = ds18x20.DS18X20(onewire.OneWire(ds_pin1))
    ds_sensor2 = ds18x20.DS18X20(onewire.OneWire(ds_pin2))
    roms1 = ds_sensor1.scan()
    roms2 = ds_sensor2.scan()
    print('Found DS devices: ', roms1)
    print('Found DS devices: ', roms2)
    if not roms1:
        print("No DS18X20 devices found. Check wiring and pull-up resistor.")
    
    # Motor setup
    fan = motorDriver.Motor(10, 9, 8)
    peltier = motorDriver.Motor(5, 6, 7)
    fan.stop()
    peltier.stop()

# WiFi setup
def setup_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(secrets.get_ID()[0], secrets.get_ID()[1])
    
    max_wait = 20  # Increased wait time
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('waiting for connection...')
        oled.text("waiting",0,0)
        oled.text("for",0,10)
        oled.text("connection..",0,20)
        time.sleep(1)
    
    if wlan.status() != 3:
        print('network connection failed')
        oled.fill(0)
        oled.text("WiFi Failed", 0, 0)
        oled.show()
        return False
    else:
        print('connected')
        status = wlan.ifconfig()
        print('ip = ' + status[0])
        oled.fill(0)
        oled.text("IP:", 0, 0)
        oled.text(status[0], 0, 10)
        oled.show()
        time.sleep(2)
        return True

# Temperature reading
def read_temperatures():
    global temp1C, temp2C
    
    try:
        ds_sensor1.convert_temp()
        ds_sensor2.convert_temp()
        time.sleep_ms(750)
        
        for rom in roms1:
            temp1C = ds_sensor1.read_temp(rom)
        for rom in roms2:
            temp2C = ds_sensor2.read_temp(rom)
            
    except Exception as e:
        print("Error reading temps:", e)

# Adaptive PELTIER control
def control_peltier():
    global fan_speed, peltier_power

    if button.value() == 1:
        toggle_mode()
    
    if current_mode == MODE_OFF:
        fan.stop()
        peltier.stop()
        fan_speed = 0
        peltier_power = 0
    else:
        # Constant max fan speed in all cooling modes
        fan_speed = 100
        fan.pwm_start(fan_speed)
        
        # Adaptive peltier control
        target_temp = TARGET_TEMPS[current_mode]
        temp_diff = temp2C - target_temp
        
        if temp_diff > 0:  # If current temp is above target
            # Calculate adaptive power (more cooling when further from target)
            max_power = 100
            min_power = 30  # Minimum power to maintain cooling
            power_range = max_power - min_power
            
            # Exponential response curve for smoother control
            adaptive_factor = min(1.0, temp_diff / 10.0)  # Scale to 0-1 range
            adaptive_factor = adaptive_factor ** 0.7  # Flatten the curve
            
            peltier_power = min_power + int(power_range * adaptive_factor)
            peltier.pwm_start(peltier_power)
        else:
            # At or below target temp - reduce power
            peltier_power = 0
            peltier.stop()

# OLED display - simplified monitoring screen
def update_display():
    global last_display_update
    
    current_time = time.ticks_ms()
    if current_time - last_display_update < 1000:  # Update every second
        return
    
    last_display_update = current_time
    
    oled.fill(0)
    
    # Display temperatures and mode
    oled.text(f"T1:{temp1C:5.1f}C", 0, 0)
    oled.text(f"T2:{temp2C:5.1f}C", 0, 10)
    oled.text(f"Mode:{MODE_NAMES[current_mode]}", 0, 20)
    
    oled.show()
    led.toggle()

# Web server functions
def web_server():
    global current_mode
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', 80))
    s.listen(5)
    
    print("Web server started")
    
    while True:
        try:
            conn, addr = s.accept()
            print('Got a connection from %s' % str(addr))
            request = conn.recv(1024)
            request = str(request)
            print('Content = %s' % request)
            
            response = ""
            
            if '/mode/off' in request:
                current_mode = MODE_OFF
                oled.progress_bar(MODE_NAMES[current_mode])
                response = get_status_json()
                
            elif '/mode/zip' in request:
                current_mode = MODE_ZIP
                oled.progress_bar(MODE_NAMES[current_mode])
                response = get_status_json()
                
            elif '/mode/zap' in request:
                current_mode = MODE_ZAP
                oled.progress_bar(MODE_NAMES[current_mode])
                response = get_status_json()
                
            elif '/mode/zoom' in request:
                current_mode = MODE_ZOOM
                oled.progress_bar(MODE_NAMES[current_mode])
                response = get_status_json()
                
            elif '/status' in request:
                response = get_status_json()
                
            else:
                response = webpage.get_webpage()
                
            conn.send('HTTP/1.1 200 OK\n')
            conn.send('Content-Type: text/html\n')
            conn.send('Connection: close\n\n')
            conn.sendall(response)
            conn.close()
            
        except Exception as e:
            print("Web server error:", e)
            try:
                conn.close()
            except:
                pass

def get_status_json():
    status = {
        "temp1": temp1C,
        "temp2": temp2C,
        "temp_diff": temp1C - temp2C,
        "mode": current_mode,
        "mode_name": MODE_NAMES[current_mode],
        "target_temp": TARGET_TEMPS[current_mode],
        "fan_speed": fan_speed,
        "peltier_power": peltier_power,
        "status": "OK"
    }
    return json.dumps(status)

# Main loop
def main_loop():
    setup_hardware()
    if not setup_wifi():
        print("Continuing without WiFi")
    
    # Start web server on second core
    try:
        _thread.start_new_thread(web_server, ())
    except Exception as e:
        print("Failed to start web server thread:", e)
    
    print("Starting main loop")
    
    while True:
        read_temperatures()
        control_peltier()
        update_display()
        time.sleep(0.1)

# Start the program
if __name__ == "__main__":
    main_loop()

