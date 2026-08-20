#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "bms_can.h"
#include "bms_link.h"

#define CHECK(condition)                                                        \
    do {                                                                        \
        if (!(condition)) {                                                     \
            fprintf(stderr, "%s:%d CHECK failed: %s\n", __FILE__, __LINE__, \
                    #condition);                                                \
            return 1;                                                           \
        }                                                                       \
    } while (0)

typedef struct {
    uint16_t id;
    uint8_t dlc;
    uint8_t data[8];
} captured_frame_t;

static captured_frame_t s_frames[8];
static size_t s_frame_count;

/* Product bms_link.c is tested unchanged. Only the hardware transport is
 * replaced, making the payload bytes the observable test oracle. */
bool bms_can_send(uint16_t id, const uint8_t *data, uint8_t dlc)
{
    captured_frame_t *frame;
    if (data == NULL || dlc > 8U || s_frame_count >= 8U) {
        return false;
    }
    frame = &s_frames[s_frame_count++];
    frame->id = id;
    frame->dlc = dlc;
    memcpy(frame->data, data, dlc);
    return true;
}

bool bms_can_init(void) { return true; }
void bms_can_poll_rx(void) { }

static void reset_capture(void)
{
    memset(s_frames, 0, sizeof(s_frames));
    s_frame_count = 0U;
}

static int test_main_payload(void)
{
    bms_data_t data;
    const uint8_t expected_main[8] = {
        0x34U, 0x12U, /* 0x1234 x 0.01 V */
        0x7BU, 0x00U, /* +123 x 0.01 A, LE */
        77U, 1U, (uint8_t)BMS_ST_CHARGE_READY, 0x81U
    };
    const uint8_t expected_state[2] = {
        (uint8_t)BMS_ST_CHARGE_READY, 0x81U
    };

    memset(&data, 0, sizeof(data));
    data.pack_mv = 0x1234 * 10;
    data.pack_ma = 1230;
    data.soc = 77U;
    data.charge_permit = true;
    data.state = BMS_ST_CHARGE_READY;
    data.fault = BMS_FLT_CELL_OV | BMS_FLT_IMBALANCE;

    reset_capture();
    bms_link_send_main(&data);
    CHECK(s_frame_count == 2U);
    CHECK(s_frames[0].id == CFG_CAN_ID_MAIN);
    CHECK(s_frames[0].dlc == 8U);
    CHECK(memcmp(s_frames[0].data, expected_main, sizeof(expected_main)) == 0);
    CHECK(s_frames[1].id == CFG_CAN_ID_STATE);
    CHECK(s_frames[1].dlc == 2U);
    CHECK(memcmp(s_frames[1].data, expected_state, sizeof(expected_state)) == 0);
    return 0;
}

static int test_cell_temperature_and_version_payloads(void)
{
    bms_data_t data;
    const uint8_t expected_cell[8] = {
        0xE4U, 0x0CU, 0xE5U, 0x0CU, 0xE6U, 0x0CU, 0xE7U, 0x0CU
    };
    const uint8_t expected_temp[8] = {
        0xFFU, 0xFFU, /* -0.1 C signed LE */
        0x03U, 0x00U, 0xE4U, 0x0CU, 0xE7U, 0x0CU
    };
    const uint8_t expected_version[4] = {
        CFG_FW_VERSION_MAJOR, CFG_FW_VERSION_MINOR, 0U, 0U
    };

    memset(&data, 0, sizeof(data));
    data.cell_mv[0] = 3300;
    data.cell_mv[1] = 3301;
    data.cell_mv[2] = 3302;
    data.cell_mv[3] = 3303;
    data.temp_c10 = -1;
    data.imbalance_mv = 3;
    data.cell_min_mv = 3300;
    data.cell_max_mv = 3303;

    reset_capture();
    bms_link_send_cell(&data);
    bms_link_send_version();
    CHECK(s_frame_count == 3U);
    CHECK(s_frames[0].id == CFG_CAN_ID_CELL && s_frames[0].dlc == 8U);
    CHECK(memcmp(s_frames[0].data, expected_cell, sizeof(expected_cell)) == 0);
    CHECK(s_frames[1].id == CFG_CAN_ID_TEMP && s_frames[1].dlc == 8U);
    CHECK(memcmp(s_frames[1].data, expected_temp, sizeof(expected_temp)) == 0);
    CHECK(s_frames[2].id == CFG_CAN_ID_VERSION && s_frames[2].dlc == 4U);
    CHECK(memcmp(s_frames[2].data, expected_version, sizeof(expected_version)) == 0);
    return 0;
}

int main(void)
{
    if (test_main_payload() != 0) {
        return 1;
    }
    if (test_cell_temperature_and_version_payloads() != 0) {
        return 1;
    }
    puts("TC-CAN-HOST-001 PASS: BMS product payload ID/DLC/LE packing");
    return 0;
}
