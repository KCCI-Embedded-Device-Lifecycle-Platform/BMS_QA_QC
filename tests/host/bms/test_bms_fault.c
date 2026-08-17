#include <stdbool.h>
#include <stdio.h>
#include <string.h>

#include "bms_fault.h"
#include "bms_oracle.h"
#include "hw_tick_mock.h"
#include "qa_requirements.h"

#define CHECK(condition) \
    do { \
        if (!(condition)) { \
            fprintf(stderr, "%s:%d CHECK failed: %s\n", __FILE__, __LINE__, #condition); \
            return false; \
        } \
    } while (0)

_Static_assert(CFG_CELL_OV_MV == QA_REQ_BMS_CELL_OV_MV, "CELL_OV requirement drift");
_Static_assert(CFG_CELL_OV_CLR_MV == QA_REQ_BMS_CELL_OV_CLEAR_MV, "CELL_OV clear drift");
_Static_assert(CFG_CELL_UV_MV == QA_REQ_BMS_CELL_UV_MV, "CELL_UV requirement drift");
_Static_assert(CFG_PACK_OV_MV == QA_REQ_BMS_PACK_OV_MV, "PACK_OV requirement drift");
_Static_assert(CFG_OVER_CURRENT_MA == QA_REQ_BMS_OVER_CURRENT_MA, "OC drift");
_Static_assert(CFG_OVER_TEMP_C10 == QA_REQ_BMS_OVER_TEMP_C10, "OT drift");
_Static_assert(CFG_SENSOR_DIFF_MA == QA_REQ_BMS_SENSOR_DIFF_MA, "sensor diff drift");
_Static_assert(CFG_FAULT_CONFIRM_CNT == QA_REQ_BMS_FAULT_CONFIRM_COUNT, "confirm drift");

static bms_data_t normal_data(void)
{
    bms_data_t data;
    uint8_t index;
    memset(&data, 0, sizeof(data));
    for (index = 0U; index < BMS_CELL_COUNT; ++index) {
        data.cell_mv[index] = 3600;
    }
    data.pack_mv = 14400;
    data.pack_ma = 0;
    data.acs_ma = 0;
    data.temp_c10 = 250;
    data.sensor_ready = true;
    data.charge_permit = true;
    return data;
}

static void init_case(bms_data_t *data)
{
    *data = normal_data();
    qa_tick_set(0U);
    bms_fault_init();
    bms_fault_notify_link();
}

static void checked_step(bms_data_t *data)
{
    qa_tick_advance(QA_REQ_BMS_FAULT_TASK_MS);
    bms_fault_notify_link();
    bms_fault_check(data);
}

static bool tc_bms_ov_001(void)
{
    bms_data_t data;
    uint8_t count;
    init_case(&data);
    for (count = 0U; count < 3U; ++count) {
        data.cell_mv[0] = 4200;
        checked_step(&data);
        CHECK((data.fault & BMS_FLT_CELL_OV) == 0U);
    }
    data.cell_mv[0] = 4201;
    CHECK(qa_bms_cell_ov_candidate(data.cell_mv[0]));
    checked_step(&data);
    CHECK((data.fault & BMS_FLT_CELL_OV) == 0U);
    return true;
}

static bool tc_bms_ov_002(void)
{
    bms_data_t data;
    init_case(&data);
    data.cell_mv[0] = 4201;
    checked_step(&data);
    checked_step(&data);
    CHECK((data.fault & BMS_FLT_CELL_OV) == 0U);
    checked_step(&data);
    CHECK((data.fault & BMS_FLT_CELL_OV) != 0U);
    return true;
}

static void set_cell_ov(bms_data_t *data)
{
    data->cell_mv[0] = 4201;
    checked_step(data);
    checked_step(data);
    checked_step(data);
}

static bool tc_bms_ov_003(void)
{
    bms_data_t data;
    uint8_t count;
    init_case(&data);
    set_cell_ov(&data);
    CHECK((data.fault & BMS_FLT_CELL_OV) != 0U);
    data.cell_mv[0] = 4150;
    for (count = 0U; count < 32U; ++count) {
        checked_step(&data);
    }
    CHECK(!qa_bms_cell_ov_clear_candidate(4150));
    CHECK((data.fault & BMS_FLT_CELL_OV) != 0U);
    data.cell_mv[0] = 4149;
    checked_step(&data);
    CHECK((data.fault & BMS_FLT_CELL_OV) != 0U);
    return true;
}

static bool tc_bms_ov_004(void)
{
    bms_data_t data;
    uint8_t count;
    init_case(&data);
    set_cell_ov(&data);
    data.cell_mv[0] = 4149;
    for (count = 0U; count < 30U; ++count) {
        checked_step(&data);
    }
    CHECK((data.fault & BMS_FLT_CELL_OV) != 0U);
    checked_step(&data);
    CHECK((data.fault & BMS_FLT_CELL_OV) == 0U);
    return true;
}

static bool tc_bms_uv_001(void)
{
    bms_data_t data;
    init_case(&data);
    data.cell_mv[0] = 3000;
    checked_step(&data);
    checked_step(&data);
    checked_step(&data);
    CHECK((data.fault & BMS_FLT_CELL_UV) == 0U);
    data.cell_mv[0] = 2999;
    checked_step(&data);
    checked_step(&data);
    CHECK((data.fault & BMS_FLT_CELL_UV) == 0U);
    checked_step(&data);
    CHECK((data.fault & BMS_FLT_CELL_UV) != 0U);
    return true;
}

static bool tc_bms_packov_001(void)
{
    bms_data_t data;
    init_case(&data);
    data.pack_mv = 16800;
    checked_step(&data);
    checked_step(&data);
    checked_step(&data);
    CHECK((data.fault & BMS_FLT_PACK_OV) == 0U);
    data.pack_mv = 16801;
    checked_step(&data);
    checked_step(&data);
    checked_step(&data);
    CHECK((data.fault & BMS_FLT_PACK_OV) != 0U);
    return true;
}

static bool tc_bms_oc_001(void)
{
    bms_data_t data;
    int32_t values[] = {1000, -1000, 1001, -1001};
    uint8_t index;
    for (index = 0U; index < 4U; ++index) {
        init_case(&data);
        data.pack_ma = values[index];
        data.acs_ma = values[index];
        checked_step(&data);
        checked_step(&data);
        checked_step(&data);
        CHECK(((data.fault & BMS_FLT_OVER_CURRENT) != 0U) ==
              qa_bms_over_current_candidate(values[index]));
    }
    return true;
}

static bool tc_bms_ot_001(void)
{
    bms_data_t data;
    uint8_t count;
    init_case(&data);
    data.temp_c10 = 550;
    checked_step(&data);
    checked_step(&data);
    checked_step(&data);
    CHECK((data.fault & BMS_FLT_OVER_TEMP) == 0U);
    data.temp_c10 = 551;
    checked_step(&data);
    checked_step(&data);
    checked_step(&data);
    CHECK((data.fault & BMS_FLT_OVER_TEMP) != 0U);
    data.temp_c10 = 500;
    for (count = 0U; count < 32U; ++count) {
        checked_step(&data);
    }
    CHECK((data.fault & BMS_FLT_OVER_TEMP) != 0U);
    data.temp_c10 = 499;
    for (count = 0U; count < 31U; ++count) {
        checked_step(&data);
    }
    CHECK((data.fault & BMS_FLT_OVER_TEMP) == 0U);
    return true;
}

static bool tc_bms_sensor_001(void)
{
    bms_data_t data;
    init_case(&data);
    data.sensor_ready = false;
    CHECK(qa_bms_sensor_fault_candidate(false, 0, 0));
    checked_step(&data);
    checked_step(&data);
    checked_step(&data);
    CHECK((data.fault & BMS_FLT_SENSOR_ERR) != 0U);

    init_case(&data);
    data.pack_ma = 0;
    data.acs_ma = 501;
    CHECK(qa_bms_sensor_fault_candidate(true, data.pack_ma, data.acs_ma));
    checked_step(&data);
    checked_step(&data);
    checked_step(&data);
    CHECK((data.fault & BMS_FLT_SENSOR_ERR) != 0U);
    return true;
}

static bool tc_bms_permit_001(void)
{
    bms_data_t data;
    uint8_t bit;
    for (bit = 0U; bit < 7U; ++bit) {
        CHECK(!qa_bms_charge_permit((uint16_t)(1U << bit)));
    }
    CHECK(qa_bms_charge_permit(0x80U)); /* imbalance is warning-only */
    init_case(&data);
    data.pack_mv = 16801;
    checked_step(&data);
    checked_step(&data);
    checked_step(&data);
    CHECK(!data.charge_permit);
    CHECK(!qa_bms_charge_permit(data.fault));
    return true;
}

static bool tc_bms_multi_001(void)
{
    bms_data_t data;
    init_case(&data);
    data.cell_mv[0] = 4201;
    data.cell_mv[1] = 2999;
    data.pack_ma = 1001;
    data.acs_ma = 1001;
    checked_step(&data);
    checked_step(&data);
    checked_step(&data);
    CHECK((data.fault & (BMS_FLT_CELL_OV | BMS_FLT_CELL_UV | BMS_FLT_OVER_CURRENT)) ==
          (BMS_FLT_CELL_OV | BMS_FLT_CELL_UV | BMS_FLT_OVER_CURRENT));
    CHECK(!data.charge_permit);
    return true;
}

typedef bool (*test_function_t)(void);

typedef struct {
    const char *id;
    test_function_t function;
} test_entry_t;

static const test_entry_t TESTS[] = {
    {"TC-BMS-OV-001", tc_bms_ov_001},
    {"TC-BMS-OV-002", tc_bms_ov_002},
    {"TC-BMS-OV-003", tc_bms_ov_003},
    {"TC-BMS-OV-004", tc_bms_ov_004},
    {"TC-BMS-UV-001", tc_bms_uv_001},
    {"TC-BMS-PACKOV-001", tc_bms_packov_001},
    {"TC-BMS-OC-001", tc_bms_oc_001},
    {"TC-BMS-OT-001", tc_bms_ot_001},
    {"TC-BMS-SENSOR-001", tc_bms_sensor_001},
    {"TC-BMS-PERMIT-001", tc_bms_permit_001},
    {"TC-BMS-MULTI-001", tc_bms_multi_001},
};

int main(int argc, char **argv)
{
    size_t index;
    if (argc != 2) {
        fprintf(stderr, "usage: %s TEST-ID\n", argv[0]);
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
    fprintf(stderr, "unknown test id: %s\n", argv[1]);
    return 2;
}
