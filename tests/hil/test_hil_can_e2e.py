import pytest
import time
try:
    import can
except ImportError:
    can = None

# TC-HIL-CAN-3NODE-001 / BEOG-48
# TC-SYS-EVSE-BMS-CHG-001 / BEOG-49

@pytest.mark.skipif(can is None, reason="python-can library not installed")
def test_beog_48_3node_can_acceptance():
    """
    [BEOG-48] 3-Node Bus Acceptance — BMS + EVSE + Raspberry Pi
    Verifies that BMS and EVSE are both broadcasting their expected periodic frames.
    """
    bus = can.interface.Bus(
        interface='seeedstudio',
        channel='/dev/ttyUSB0',
        baudrate=2_000_000,
        bitrate=500_000,
        operation_mode='normal',
        timeout=0.1
    )
    
    seen_bms_100 = False
    seen_evse_200 = False
    
    start_time = time.time()
    # Listen for up to 3 seconds
    while time.time() - start_time < 3.0:
        msg = bus.recv(timeout=0.5)
        if msg:
            if msg.arbitration_id == 0x100:
                seen_bms_100 = True
            elif msg.arbitration_id == 0x200:
                seen_evse_200 = True
                
        if seen_bms_100 and seen_evse_200:
            break
            
    bus.shutdown()
    
    assert seen_bms_100, "BMS 0x100 frame not seen! Check BMS power and CAN termination."
    assert seen_evse_200, "EVSE 0x200 frame not seen! Check EVSE power and CAN termination."


@pytest.mark.skipif(can is None, reason="python-can library not installed")
def test_beog_49_evse_start_stop():
    """
    [BEOG-49] EVSE START/STOP -> 0x201 -> BMS Relay PA8 E2E
    Listens for the 0x201 START command from EVSE.
    Note: Requires manual or GPIO-triggered button press on EVSE PE13 during the 10s window.
    """
    bus = can.interface.Bus(
        interface='seeedstudio',
        channel='/dev/ttyUSB0',
        baudrate=2_000_000,
        bitrate=500_000,
        operation_mode='normal',
        timeout=0.1
    )
    
    seen_start = False
    
    print("\n[HIL ACTION REQUIRED] Press EVSE START button (PE13 -> GND) NOW!")
    print("Waiting up to 10 seconds for 0x201 DLC=1 Data[0]=1...")
    
    start_time = time.time()
    while time.time() - start_time < 10.0:
        msg = bus.recv(timeout=0.5)
        if msg and msg.arbitration_id == 0x201:
            if len(msg.data) >= 1 and msg.data[0] == 1:
                seen_start = True
                print("SUCCESS: Observed EVSE 0x201 START request!")
                break
                
    bus.shutdown()
    
    assert seen_start, "Did not observe 0x201 START request within 10 seconds. Did you press the button?"
