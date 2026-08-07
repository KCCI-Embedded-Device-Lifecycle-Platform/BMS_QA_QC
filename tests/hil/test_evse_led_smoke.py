import serial, time
import RPi.GPIO as GPIO

PORT = "/dev/ttyUSB0"
LED_SENSE_PIN = 17

GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_SENSE_PIN, GPIO.IN)

def send_cmd(cmd: bytes) -> str:
    with serial.Serial(PORT, 115200, timeout=1) as ser:
        ser.write(cmd)
        time.sleep(0.1)
        return ser.readline().decode().strip()

def test_led_on():
    assert send_cmd(b'L') == "LED=1"          # 펌웨어 자체 보고
    assert GPIO.input(LED_SENSE_PIN) == GPIO.HIGH  # 실제 전기 신호 확인

def test_led_off():
    assert send_cmd(b'O') == "LED=0"
    assert GPIO.input(LED_SENSE_PIN) == GPIO.LOW