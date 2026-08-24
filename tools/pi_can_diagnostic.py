#!/usr/bin/env python3
import time
import glob
import can

def get_usb_can_port():
    ports = glob.glob('/dev/ttyUSB*')
    if ports:
        ports.sort(reverse=True)
        return ports[0]
    return '/dev/ttyUSB0'

def main():
    port = get_usb_can_port()
    print(f"=======================================")
    print(f"🚀 라즈베리파이 CAN 진단 테스트 시작 🚀")
    print(f"=======================================")
    print(f"[1] USB 포트 자동 감지: {port}")
    
    try:
        bus = can.interface.Bus(
            interface='seeedstudio',
            channel=port,
            baudrate=2_000_000,
            bitrate=500_000,
            operation_mode='normal', # ACK 활성화 (Bus-Off 방지)
            timeout=0.1
        )
    except Exception as e:
        print(f"❌ CAN 어댑터 연결 실패: {e}")
        return

    print(f"[2] 노드 상태 모니터링 (3초간 수신 대기...)")
    seen_bms = False
    seen_evse = False
    start_time = time.time()
    
    while time.time() - start_time < 3.0:
        msg = bus.recv(timeout=0.2)
        if msg:
            if msg.arbitration_id == 0x100:
                seen_bms = True
            elif msg.arbitration_id == 0x200:
                seen_evse = True
                
    if seen_bms and seen_evse:
        print(f"✅ BMS(0x100) 및 EVSE(0x200) 정상 수신 완료!")
    else:
        print(f"⚠️ 경고: 수신 상태 불량 (BMS: {seen_bms}, EVSE: {seen_evse})")
        print(f"   -> 양쪽 보드 전원 및 120옴 종단 저항을 확인해주세요.")
        
    print(f"\n[3] 가상 EVSE START 신호 주입 (버튼 클릭 시뮬레이션)")
    # 0x201 (DLC=1, Data=1) 전송
    start_msg = can.Message(arbitration_id=0x201, is_extended_id=False, data=[1])
    bus.send(start_msg)
    print(f"✅ 0x201 (START) 메시지 버스에 주입 완료!")
    
    print(f"\n[4] 통신 종료 및 어댑터 반환")
    bus.shutdown()
    print(f"✅ 테스트 스크립트 정상 종료. (BMS 보드의 릴레이 소리를 확인해보세요!)")

if __name__ == "__main__":
    main()
