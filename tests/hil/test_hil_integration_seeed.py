#!/usr/bin/env python3
"""Automated BMS-EVSE-Seeed analyzer integration test."""

from __future__ import annotations

import argparse
import sys
import time
from collections import Counter

import can

from can_common import (
    BITRATE,
    EVSE_START,
    EVSE_STOP,
    ID_BMS_STATUS,
    ID_BMS_TEST_RESPONSE,
    ID_EVSE_STATUS,
    ID_EVSE_TEST_RESPONSE,
    TARGET_BMS,
    TARGET_EVSE,
    build_evse_control,
    build_test_request,
    decode_bms_status,
    decode_evse_status,
    drain_rx,
    frame_text,
    managed_seeed_bus,
    wait_for_id,
)


def check_periodic_frames(bus: can.BusABC, duration_s: float) -> bool:
    counts: Counter[int] = Counter()
    last_counter: dict[int, int] = {}
    counter_gaps: Counter[int] = Counter()
    deadline = time.monotonic() + duration_s

    while time.monotonic() < deadline:
        msg = bus.recv(timeout=0.1)
        if msg is None or msg.arbitration_id not in (ID_BMS_STATUS, ID_EVSE_STATUS):
            continue
        if msg.dlc != 8:
            print(f"FAIL: status DLC is {msg.dlc}, expected 8: {frame_text(msg)}")
            return False

        can_id = msg.arbitration_id
        counter = msg.data[7]
        if can_id in last_counter:
            expected = (last_counter[can_id] + 1) & 0xFF
            if counter != expected:
                counter_gaps[can_id] += 1
        last_counter[can_id] = counter
        counts[can_id] += 1

    minimum = max(1, int(duration_s * 8.0))
    print(
        f"Periodic counts: BMS={counts[ID_BMS_STATUS]}, "
        f"EVSE={counts[ID_EVSE_STATUS]}, required>={minimum}"
    )
    print(
        f"Counter gaps: BMS={counter_gaps[ID_BMS_STATUS]}, "
        f"EVSE={counter_gaps[ID_EVSE_STATUS]}"
    )
    return (
        counts[ID_BMS_STATUS] >= minimum
        and counts[ID_EVSE_STATUS] >= minimum
        and counter_gaps[ID_BMS_STATUS] == 0
        and counter_gaps[ID_EVSE_STATUS] == 0
    )


def check_echo(
    bus: can.BusABC,
    *,
    target: int,
    response_id: int,
    label: str,
    sequence: int,
) -> bool:
    request = build_test_request(target, sequence)
    bus.send(request)
    response = wait_for_id(
        bus,
        response_id,
        timeout_s=1.0,
        sequence=sequence,
    )
    if response is None:
        print(f"FAIL: {label} echo response 0x{response_id:03X} not received")
        return False
    if response.dlc != 8 or response.data[0] != target or response.data[1] != 0xA5:
        print(f"FAIL: malformed {label} echo: {frame_text(response)}")
        return False
    print(f"PASS: {label} echo: {frame_text(response)}")
    return True


def check_evse_command(
    bus: can.BusABC,
    *,
    command: int,
    expected_state: int,
    sequence: int,
) -> bool:
    bus.send(build_evse_control(command, sequence))
    deadline = time.monotonic() + 1.0
    while time.monotonic() < deadline:
        msg = bus.recv(timeout=0.1)
        if msg is None or msg.arbitration_id != ID_EVSE_STATUS or msg.dlc != 8:
            continue
        status = decode_evse_status(msg)
        if status.command_sequence != sequence:
            continue
        if status.state != expected_state:
            print(
                f"FAIL: EVSE state={status.state}, expected={expected_state}, "
                f"fault=0x{status.fault_bits:02X}, bms_alive={status.bms_alive}"
            )
            return False
        print(f"PASS: EVSE command={command}, state={status.state}")
        return True
    print("FAIL: EVSE did not acknowledge command in status frame")
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--channel", default="/dev/ttyUSB0")
    parser.add_argument("--bitrate", type=int, default=BITRATE)
    parser.add_argument("--observe-seconds", type=float, default=5.0)
    parser.add_argument(
        "--passive-only",
        action="store_true",
        help="Only verify periodic 0x100/0x200 frames; do not inject commands.",
    )
    args = parser.parse_args()

    results: list[tuple[str, bool]] = []
    try:
        with managed_seeed_bus(args.channel, bitrate=args.bitrate) as bus:
            time.sleep(0.2)
            drain_rx(bus)

            print("TC-01: periodic BMS/EVSE status frames")
            results.append(("periodic status", check_periodic_frames(bus, args.observe_seconds)))

            if not args.passive_only:
                print("TC-02: BMS request/response")
                results.append((
                    "BMS echo",
                    check_echo(
                        bus,
                        target=TARGET_BMS,
                        response_id=ID_BMS_TEST_RESPONSE,
                        label="BMS",
                        sequence=0x11,
                    ),
                ))

                print("TC-03: EVSE request/response")
                results.append((
                    "EVSE echo",
                    check_echo(
                        bus,
                        target=TARGET_EVSE,
                        response_id=ID_EVSE_TEST_RESPONSE,
                        label="EVSE",
                        sequence=0x22,
                    ),
                ))

                print("TC-04: EVSE START command")
                results.append((
                    "EVSE start",
                    check_evse_command(
                        bus,
                        command=EVSE_START,
                        expected_state=EVSE_START,
                        sequence=0x31,
                    ),
                ))

                print("TC-05: EVSE STOP command")
                results.append((
                    "EVSE stop",
                    check_evse_command(
                        bus,
                        command=EVSE_STOP,
                        expected_state=EVSE_STOP,
                        sequence=0x32,
                    ),
                ))

    except (can.CanError, OSError, ValueError) as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return 2

    print("\n=== RESULT ===")
    for name, passed in results:
        print(f"{'PASS' if passed else 'FAIL'}  {name}")
    return 0 if results and all(passed for _, passed in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())

