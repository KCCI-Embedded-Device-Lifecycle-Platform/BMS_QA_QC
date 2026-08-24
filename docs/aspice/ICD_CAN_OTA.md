# Interface Control Document — CAN / OTA

문서 ID: `BEOG-ICD-001`
상태: CAN baseline candidate; OTA security extension pending

## CAN physical/data link

| 항목 | 값 |
|---|---|
| Bitrate | 500,000 bit/s |
| Frame | Classic CAN, 11-bit Standard, Data frame |
| Nominal termination | 전원 OFF DMM 60 Ω, acceptance 54–66 Ω |
| Byte order | little-endian |
| Signed field | pack current = signed int16, 10 mA/LSB |

## BMS → EVSE

| ID | DLC | Period | 주요 payload |
|---|---:|---:|---|
| 0x100 | 8 | 100 ms | pack voltage[0:1], current[2:3], SOC[4], permit[5], BMS state[6], faults[7] |
| 0x101 | 8 | 500 ms | cell voltages; product header가 정의한 LE layout |
| 0x102 | 8 | 500 ms | temperatures; product header가 정의한 layout |
| 0x103 | 8 | 100 ms | detailed BMS state/status |
| 0x104 | 8 | 1000 ms | version |
| 0x105 | variable by command | event | BMS response; 명령별 DLC를 test vector에 고정 |

## EVSE → BMS

| ID | DLC | 의미 |
|---|---:|---|
| 0x200 | 4 | EVSE state, relay **command**, connector/status |
| 0x201 | 1 | charge request: START=1, STOP=0 |
| 0x202 | 1 | EVSE fault bitmask |
| 0x203 | 0 | BMS OTA enter request; current BMS candidate rejects it |
| 0x204 | command-defined | OTA data placeholder; DLC/flow not approved for application E2E |
| 0x205 | 4 | BMS parameter write |

0x200 data[1]은 물리 contactor feedback이 아니다. 시스템 시험에서 이 필드를
PE11 또는 실제 contactor 상태의 대체 오라클로 사용하면 false PASS다.

## Negative behavior

- Extended/RTR/error frame과 잘못된 DLC는 state mutation 없이 INVALID 처리한다.
- 알려지지 않은 standard ID는 state mutation 없이 IGNORED 처리한다.
- cached 0x100은 새 0x201 request의 acknowledgement가 아니다. request 송신 뒤
  증가한 RX sequence와 허용 state가 함께 확인되어야 한다.

## OTA memory map

| 영역 | 시작 | 끝(미포함) | 크기 |
|---|---:|---:|---:|
| Bootloader | 0x08000000 | 0x08020000 | 128 KiB |
| Application | 0x08020000 | 0x08100000 | 896 KiB |
| Staging | 0x08100000 | 0x081E0000 | 896 KiB |
| Reserved/metadata | 0x081E0000 | 0x08200000 | 128 KiB |

EVSE application linker가 0x08100000을 넘는 이미지를 허용하면 staging과 충돌한다.
CI artifact gate는 BIN 크기와 vector start를 검사해야 한다.

## Binary boot protocol

```text
SOF1 AA | SOF2 55 | command u8 | length u16 LE | data[0..512] | CRC16 u16 LE
```

Commands: `01 HELLO`, `02 VERSION`, `10 START_UPDATE`, `11 DATA`,
`12 END_UPDATE`, `13 ABORT`, `20 RUN_APP`, `79 ACK`, `1F NACK`,
`82 VERSION_RESPONSE`. CRC16은 command부터 data까지 CCITT-FALSE로 계산한다.

Whole-image CRC32, image length 및 순차 offset이 모두 유효하기 전에는 app vector
8 byte를 기록하지 않는다. Version, signature, target ID, anti-rollback은 현재 wire
contract에 없으므로 시험에서 존재한다고 가정하지 않는다.
