#include <stdbool.h>
#include <stdio.h>
#include <string.h>

#include "bms_state.h"

#define CHECK(condition) \
    do { if (!(condition)) { \
        fprintf(stderr, "%s:%d CHECK failed: %s\n", __FILE__, __LINE__, #condition); \
        return 1; \
    } } while (0)

int main(void)
{
    bms_data_t data;
    uint8_t index;
    memset(&data, 0, sizeof(data));
    data.sensor_ready = true;
    for (index = 0U; index < BMS_CELL_COUNT; ++index) {
        data.cell_mv[index] = 3600;
    }

    bms_fsm_init(&data);
    CHECK(data.state == BMS_ST_INIT);
    CHECK(!data.charge_permit);
    bms_fsm_run(&data);
    CHECK(data.state == BMS_ST_SELF_CHECK);
    bms_fsm_run(&data);
    CHECK(data.state == BMS_ST_IDLE);

    data.charge_permit = true;
    data.evse_charge_req = true;
    bms_fsm_run(&data);
    CHECK(data.state == BMS_ST_CHARGE_READY);
    data.pack_ma = 101;
    bms_fsm_run(&data);
    CHECK(data.state == BMS_ST_CHARGING);

    data.fault = BMS_FLT_CELL_OV;
    bms_fsm_run(&data);
    CHECK(data.state == BMS_ST_FAULT);
    CHECK(!data.charge_permit);
    data.fault = BMS_FLT_NONE;
    data.charge_permit = true;
    bms_fsm_run(&data);
    CHECK(data.state == BMS_ST_IDLE);
    CHECK(!data.charge_permit);

    puts("PASS TC-BMS-FSM-001");
    return 0;
}
