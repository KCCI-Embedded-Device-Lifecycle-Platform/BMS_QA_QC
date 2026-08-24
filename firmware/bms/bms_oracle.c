#include "bms_oracle.h"

#include "qa_requirements.h"

static int32_t qa_abs_i32(int32_t value)
{
    return value < 0 ? -value : value;
}

bool qa_bms_cell_ov_candidate(int32_t cell_mv)
{
    return cell_mv > QA_REQ_BMS_CELL_OV_MV;
}

bool qa_bms_cell_ov_clear_candidate(int32_t cell_mv)
{
    return cell_mv < QA_REQ_BMS_CELL_OV_CLEAR_MV;
}

bool qa_bms_cell_uv_candidate(int32_t cell_mv)
{
    return cell_mv < QA_REQ_BMS_CELL_UV_MV;
}

bool qa_bms_cell_uv_clear_candidate(int32_t cell_mv)
{
    return cell_mv > QA_REQ_BMS_CELL_UV_CLEAR_MV;
}

bool qa_bms_pack_ov_candidate(int32_t pack_mv)
{
    return pack_mv > QA_REQ_BMS_PACK_OV_MV;
}

bool qa_bms_over_current_candidate(int32_t pack_ma)
{
    return qa_abs_i32(pack_ma) > QA_REQ_BMS_OVER_CURRENT_MA;
}

bool qa_bms_over_temp_candidate(int32_t temp_c10)
{
    return temp_c10 > QA_REQ_BMS_OVER_TEMP_C10;
}

bool qa_bms_sensor_fault_candidate(bool sensor_ready, int32_t shunt_ma, int32_t hall_ma)
{
    return !sensor_ready ||
           qa_abs_i32(shunt_ma - hall_ma) > QA_REQ_BMS_SENSOR_DIFF_MA;
}

bool qa_bms_charge_permit(uint16_t fault_bits)
{
    return (fault_bits & QA_REQ_BMS_FAULT_CRITICAL_MASK) == 0U;
}
