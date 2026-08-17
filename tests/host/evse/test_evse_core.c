#include <stdbool.h>
#include <stdio.h>
#include <string.h>

#include "can_protocol.h"
#include "evse_fsm.h"
#include "evse_oracle.h"
#include "qa_requirements.h"

#define CHECK(condition) \
    do { if (!(condition)) { \
        fprintf(stderr, "%s:%d CHECK failed: %s\n", __FILE__, __LINE__, #condition); \
        return false; \
    } } while (0)

_Static_assert(CAN_ID_BMS_MAIN == QA_REQ_CAN_ID_BMS_MAIN, "BMS MAIN ID drift");
_Static_assert(CAN_ID_BMS_CELL == QA_REQ_CAN_ID_BMS_CELL, "BMS CELL ID drift");
_Static_assert(CAN_ID_BMS_TEMP == QA_REQ_CAN_ID_BMS_TEMP, "BMS TEMP ID drift");
_Static_assert(CAN_ID_BMS_STATE == QA_REQ_CAN_ID_BMS_STATE, "BMS STATE ID drift");
_Static_assert(CAN_ID_BMS_VERSION == QA_REQ_CAN_ID_BMS_VERSION, "BMS VERSION ID drift");
_Static_assert(CAN_ID_BMS_RESPONSE == QA_REQ_CAN_ID_BMS_RESPONSE, "BMS RESP ID drift");
_Static_assert(CAN_ID_EVSE_STATUS == QA_REQ_CAN_ID_EVSE_STATUS, "EVSE STATUS ID drift");
_Static_assert(CAN_ID_EVSE_CHARGE_REQUEST == QA_REQ_CAN_ID_EVSE_REQUEST, "request ID drift");
_Static_assert(CAN_ID_EVSE_FAULT == QA_REQ_CAN_ID_EVSE_FAULT, "fault ID drift");
_Static_assert(CAN_ID_BMS_OTA_ENTER == QA_REQ_CAN_ID_OTA_ENTER, "OTA ENTER ID drift");
_Static_assert(CAN_ID_BMS_PARAM_WRITE == QA_REQ_CAN_ID_PARAM_WRITE, "PARAM ID drift");
_Static_assert(CAN_DLC_BMS_MAIN == QA_REQ_CAN_DLC_BMS_MAIN, "BMS MAIN DLC drift");
_Static_assert(CAN_DLC_BMS_CELL == QA_REQ_CAN_DLC_BMS_CELL, "BMS CELL DLC drift");
_Static_assert(CAN_DLC_BMS_TEMP == QA_REQ_CAN_DLC_BMS_TEMP, "BMS TEMP DLC drift");
_Static_assert(CAN_DLC_BMS_STATE == QA_REQ_CAN_DLC_BMS_STATE, "BMS STATE DLC drift");
_Static_assert(CAN_DLC_BMS_VERSION == QA_REQ_CAN_DLC_BMS_VERSION, "BMS VERSION DLC drift");
_Static_assert(CAN_DLC_BMS_RESPONSE == QA_REQ_CAN_DLC_BMS_RESPONSE, "BMS RESP DLC drift");
_Static_assert(CAN_DLC_EVSE_STATUS == QA_REQ_CAN_DLC_EVSE_STATUS, "EVSE STATUS DLC drift");
_Static_assert(CAN_DLC_EVSE_CHARGE_REQUEST == QA_REQ_CAN_DLC_EVSE_REQUEST, "request DLC drift");
_Static_assert(CAN_DLC_EVSE_FAULT == QA_REQ_CAN_DLC_EVSE_FAULT, "fault DLC drift");
_Static_assert(CAN_DLC_BMS_OTA_ENTER == QA_REQ_CAN_DLC_OTA_ENTER, "OTA ENTER DLC drift");
_Static_assert(CAN_DLC_BMS_PARAM_WRITE == QA_REQ_CAN_DLC_PARAM_WRITE, "PARAM DLC drift");
_Static_assert(CAN_ID_BMS_OTA_DATA == QA_REQ_CAN_ID_OTA_DATA, "OTA DATA ID drift");

static can_frame_t base_main_frame(void)
{
    can_frame_t frame;
    memset(&frame, 0, sizeof(frame));
    frame.id = CAN_ID_BMS_MAIN;
    frame.dlc = CAN_DLC_BMS_MAIN;
    frame.data[0] = 0x34U;
    frame.data[1] = 0x12U;
    frame.data[2] = 0x38U;
    frame.data[3] = 0xFFU; /* -200 in signed little endian */
    frame.data[4] = 77U;
    frame.data[5] = 1U;
    frame.data[6] = (uint8_t)CAN_BMS_STATE_CHARGE_READY;
    frame.data[7] = CAN_BMS_FAULT_IMBALANCE;
    return frame;
}

static bool tc_can_proto_001(void)
{
    const uint32_t ids[] = {
        CAN_ID_BMS_MAIN, CAN_ID_BMS_CELL, CAN_ID_BMS_TEMP, CAN_ID_BMS_STATE,
        CAN_ID_BMS_VERSION, CAN_ID_BMS_RESPONSE, CAN_ID_EVSE_STATUS,
        CAN_ID_EVSE_CHARGE_REQUEST, CAN_ID_EVSE_FAULT, CAN_ID_BMS_OTA_ENTER,
        CAN_ID_BMS_OTA_DATA, CAN_ID_BMS_PARAM_WRITE
    };
    size_t left;
    size_t right;
    for (left = 0U; left < sizeof(ids) / sizeof(ids[0]); ++left) {
        CHECK(ids[left] <= 0x7FFU);
        for (right = left + 1U; right < sizeof(ids) / sizeof(ids[0]); ++right) {
            CHECK(ids[left] != ids[right]);
        }
    }
    return true;
}

static bool tc_can_endian_001(void)
{
    can_frame_t frame = base_main_frame();
    bms_snapshot_t snapshot;
    memset(&snapshot, 0, sizeof(snapshot));
    CHECK(can_protocol_decode_bms(&frame, &snapshot, 1234U) == CAN_PROTOCOL_DECODE_UPDATED);
    CHECK(snapshot.pack_voltage_10mV == 0x1234U);
    CHECK(snapshot.pack_current_10mA == -200);
    CHECK(snapshot.soc_percent == 77U);
    CHECK(snapshot.charge_permit);
    CHECK(snapshot.last_rx_tick == 1234U);
    return true;
}

static bool invalid_keeps_snapshot(can_frame_t frame)
{
    bms_snapshot_t before;
    bms_snapshot_t after;
    memset(&before, 0x5A, sizeof(before));
    after = before;
    CHECK(can_protocol_decode_bms(&frame, &after, 999U) == CAN_PROTOCOL_DECODE_INVALID);
    CHECK(memcmp(&before, &after, sizeof(before)) == 0);
    return true;
}

static bool tc_can_neg_001(void)
{
    can_frame_t frame = base_main_frame();
    frame.dlc = 7U;
    CHECK(invalid_keeps_snapshot(frame));
    frame = base_main_frame();
    frame.is_extended_id = true;
    CHECK(invalid_keeps_snapshot(frame));
    frame = base_main_frame();
    frame.is_remote_frame = true;
    CHECK(invalid_keeps_snapshot(frame));
    return true;
}

static bool tc_can_unkid_001(void)
{
    can_frame_t frame = base_main_frame();
    bms_snapshot_t before;
    bms_snapshot_t after;
    frame.id = 0x321U;
    memset(&before, 0xA5, sizeof(before));
    after = before;
    CHECK(can_protocol_decode_bms(&frame, &after, 100U) == CAN_PROTOCOL_DECODE_IGNORED);
    CHECK(memcmp(&before, &after, sizeof(before)) == 0);
    return true;
}

static bool tc_can_e2e_001(void)
{
    can_frame_t frame = base_main_frame();
    bms_snapshot_t snapshot;
    memset(&snapshot, 0, sizeof(snapshot));
    CHECK(can_protocol_decode_bms(&frame, &snapshot, 500U) == CAN_PROTOCOL_DECODE_UPDATED);
    CHECK(snapshot.online);
    CHECK(snapshot.rx_sequence == 1U);
    CHECK(snapshot.charge_permit);
    CHECK(snapshot.bms_state == (uint8_t)CAN_BMS_STATE_CHARGE_READY);
    CHECK(snapshot.fault_bits == CAN_BMS_FAULT_IMBALANCE);
    return true;
}

static bool tc_evse_safe_002(void)
{
    evse_status_t status;
    memset(&status, 0, sizeof(status));
    evse_fsm_init(&status);
    status.state = EVSE_STATE_CHARGE_READY;
    status.inputs.connector_connected = true;
    status.bms.online = true;
    status.bms.charge_permit = false;
    status.relay_command_on = true;
    evse_fsm_step(&status, EVSE_EVENT_NONE);
    CHECK(!status.relay_command_on);
    CHECK(status.state != EVSE_STATE_CHARGING);
    return true;
}

static bool tc_evse_safe_001(void)
{
    evse_status_t status;
    memset(&status, 0xA5, sizeof(status));
    evse_fsm_init(&status);
    CHECK(status.state == EVSE_STATE_INIT);
    CHECK(!status.relay_command_on);
    CHECK(status.fault_bits == EVSE_FAULT_NONE);
    return true;
}

static bool tc_evse_safe_003(void)
{
    unsigned mask;
    for (mask = 0U; mask < 64U; ++mask) {
        evse_status_t status;
        qa_evse_charge_conditions_t oracle;
        memset(&status, 0, sizeof(status));
        status.inputs.connector_connected = (mask & 0x01U) != 0U;
        status.bms.online = (mask & 0x02U) != 0U;
        status.bms.charge_permit = (mask & 0x04U) != 0U;
        status.inputs.estop_active = (mask & 0x08U) != 0U;
        status.fault_bits = (mask & 0x10U) != 0U ? EVSE_FAULT_INTERNAL : EVSE_FAULT_NONE;
        status.ota_requested = (mask & 0x20U) != 0U;
        oracle.connector_connected = status.inputs.connector_connected;
        oracle.bms_online = status.bms.online;
        oracle.charge_permit = status.bms.charge_permit;
        oracle.estop_active = status.inputs.estop_active;
        oracle.fault_bits = status.fault_bits;
        oracle.ota_requested = status.ota_requested;
        CHECK(evse_fsm_charge_conditions_met(&status) == qa_evse_charge_allowed(&oracle));
    }
    return true;
}

static bool tc_evse_safe_004(void)
{
    evse_status_t status;
    memset(&status, 0, sizeof(status));
    status.state = EVSE_STATE_CHARGING;
    status.inputs.connector_connected = true;
    status.inputs.estop_active = true;
    status.bms.online = true;
    status.bms.charge_permit = true;
    status.relay_command_on = true;
    evse_fsm_step(&status, EVSE_EVENT_NONE);
    CHECK(!status.relay_command_on);
    CHECK(status.state == EVSE_STATE_FAULT);
    return true;
}

static bool tc_evse_safe_005(void)
{
    evse_status_t status;
    CHECK(!qa_evse_bms_timed_out(QA_REQ_EVSE_BMS_TIMEOUT_MS, 0U));
    CHECK(qa_evse_bms_timed_out(QA_REQ_EVSE_BMS_TIMEOUT_MS + 1U, 0U));
    memset(&status, 0, sizeof(status));
    status.state = EVSE_STATE_CHARGING;
    status.inputs.connector_connected = true;
    status.bms.online = false;
    status.bms.charge_permit = true;
    status.relay_command_on = true;
    evse_fsm_step(&status, EVSE_EVENT_NONE);
    CHECK(!status.relay_command_on);
    CHECK(status.state == EVSE_STATE_FAULT);
    return true;
}

static bool tc_evse_safe_006(void)
{
    evse_status_t status;
    unsigned iteration;
    for (iteration = 0U; iteration < 3U; ++iteration) {
        memset(&status, 0xA5, sizeof(status));
        evse_fsm_init(&status);
        CHECK(!status.relay_command_on);
        CHECK(status.state == EVSE_STATE_INIT);
    }
    return true;
}

static bool tc_evse_fault_001(void)
{
    const evse_fault_bits_t product_bits[] = {
        EVSE_FAULT_ESTOP, EVSE_FAULT_CONNECTOR_LOST, EVSE_FAULT_BMS_TIMEOUT,
        EVSE_FAULT_BMS_REPORTED, EVSE_FAULT_CAN_BUS_OFF, EVSE_FAULT_RELAY_MISMATCH,
        EVSE_FAULT_RS485_PROTOCOL, EVSE_FAULT_INTERNAL
    };
    const uint8_t wire_bits[] = {0x01U, 0x02U, 0x04U, 0x08U, 0x10U, 0x20U, 0x40U, 0x80U};
    evse_status_t status;
    can_frame_t frame;
    size_t index;
    memset(&status, 0, sizeof(status));
    for (index = 0U; index < sizeof(product_bits) / sizeof(product_bits[0]); ++index) {
        status.fault_bits = product_bits[index];
        CHECK(can_protocol_encode_evse_fault(&status, &frame));
        CHECK(frame.id == CAN_ID_EVSE_FAULT);
        CHECK(frame.dlc == 1U);
        CHECK(frame.data[0] == wire_bits[index]);
    }
    return true;
}

static bool tc_evse_ack_gate(void);

static bool tc_evse_can_req_001(void)
{
    can_frame_t frame;
    CHECK(can_protocol_encode_charge_request(true, &frame));
    CHECK(frame.id == CAN_ID_EVSE_CHARGE_REQUEST && frame.dlc == 1U && frame.data[0] == 1U);
    CHECK(can_protocol_encode_charge_request(false, &frame));
    CHECK(frame.id == CAN_ID_EVSE_CHARGE_REQUEST && frame.dlc == 1U && frame.data[0] == 0U);
    /* Regression subcase: a cached BMS frame is not accepted as a fresh ACK. */
    CHECK(tc_evse_ack_gate());
    return true;
}

static bool tc_evse_ack_gate(void)
{
    evse_status_t status;
    memset(&status, 0, sizeof(status));
    evse_fsm_init(&status);
    status.state = EVSE_STATE_CHARGE_READY;
    status.inputs.connector_connected = true;
    status.bms.online = true;
    status.bms.charge_permit = true;
    status.bms.bms_state = (uint8_t)CAN_BMS_STATE_CHARGE_READY;
    status.bms.rx_sequence = 10U;
    evse_fsm_step(&status, EVSE_EVENT_START_REQUEST);
    CHECK(status.charge_request);
    CHECK(!status.relay_command_on);
    status.charge_request_transmitted = true;
    status.charge_request_rx_sequence = 10U;
    evse_fsm_step(&status, EVSE_EVENT_NONE);
    CHECK(!status.relay_command_on); /* cached BMS frame cannot ACK */
    status.bms.rx_sequence = 11U;
    evse_fsm_step(&status, EVSE_EVENT_NONE);
    CHECK(status.relay_command_on);
    CHECK(status.state == EVSE_STATE_CHARGING);
    return true;
}

typedef bool (*test_function_t)(void);
typedef struct { const char *id; test_function_t function; } test_entry_t;

static const test_entry_t TESTS[] = {
    {"TC-CAN-PROTO-001", tc_can_proto_001},
    {"TC-CAN-ENDIAN-001", tc_can_endian_001},
    {"TC-CAN-NEG-001", tc_can_neg_001},
    {"TC-CAN-UNKID-001", tc_can_unkid_001},
    {"TC-CAN-E2E-001", tc_can_e2e_001},
    {"TC-EVSE-SAFE-001", tc_evse_safe_001},
    {"TC-EVSE-SAFE-002", tc_evse_safe_002},
    {"TC-EVSE-SAFE-003", tc_evse_safe_003},
    {"TC-EVSE-SAFE-004", tc_evse_safe_005}, /* offline component response */
    {"TC-EVSE-SAFE-005", tc_evse_safe_004}, /* fault component response */
    {"TC-EVSE-SAFE-006", tc_evse_safe_006},
    {"TC-EVSE-FAULT-001", tc_evse_fault_001},
    {"TC-EVSE-CAN-REQ-001", tc_evse_can_req_001},
};

int main(int argc, char **argv)
{
    size_t index;
    if (argc != 2) {
        return 2;
    }
    for (index = 0U; index < sizeof(TESTS) / sizeof(TESTS[0]); ++index) {
        if (strcmp(argv[1], TESTS[index].id) == 0) {
            if (!TESTS[index].function()) {
                return 1;
            }
            printf("PASS %s\n", TESTS[index].id);
            return 0;
        }
    }
    return 2;
}
