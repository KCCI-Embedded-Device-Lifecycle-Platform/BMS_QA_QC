import time
import argparse
import can
import glob

def get_usb_can_port():
    ports = glob.glob('/dev/ttyUSB*')
    if ports:
        ports.sort(reverse=True)
        return ports[0]
    return '/dev/ttyUSB0'

def main():
    parser = argparse.ArgumentParser(description="Simulate EVSE START button via CAN")
    parser.add_argument("--channel", default=get_usb_can_port(), help="CAN interface")
    args = parser.parse_args()

    print(f"Opening CAN on {args.channel}...")
    bus = can.interface.Bus(
        interface='seeedstudio',
        channel=args.channel,
        baudrate=2_000_000,
        bitrate=500_000,
        operation_mode='normal',
        timeout=0.1
    )

    print("Sending Simulated EVSE START command (0x201 DLC=1 Data=[1])...")
    # Simulate EVSE sending the Charge Request (Start)
    msg = can.Message(arbitration_id=0x201, is_extended_id=False, data=[1])
    bus.send(msg)
    time.sleep(0.1)

    print("Listening for BMS response or Relay state change...")
    # Optionally, we can sniff 0x100 to see if BMS permit drops or relay clicks
    # Since BMS doesn't output relay state on CAN yet, we just verify the message is sent.
    
    start_time = time.time()
    seen = 0
    while time.time() - start_time < 2.0:
        rx = bus.recv(timeout=0.5)
        if rx:
            seen += 1
            if rx.arbitration_id == 0x100:
                print("BMS Status (0x100) received. The BMS relay should now be closed (ON).")
                break

    bus.shutdown()
    print("Test Complete. Check if the BMS relay physically clicked!")

if __name__ == "__main__":
    main()
