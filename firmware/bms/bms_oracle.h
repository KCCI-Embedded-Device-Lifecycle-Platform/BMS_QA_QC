#ifndef QA_BMS_ORACLE_H
#define QA_BMS_ORACLE_H

#include <stdbool.h>
#include <stdint.h>

bool qa_bms_cell_ov_candidate(int32_t cell_mv);
bool qa_bms_cell_ov_clear_candidate(int32_t cell_mv);
bool qa_bms_cell_uv_candidate(int32_t cell_mv);
bool qa_bms_cell_uv_clear_candidate(int32_t cell_mv);
bool qa_bms_pack_ov_candidate(int32_t pack_mv);
bool qa_bms_over_current_candidate(int32_t pack_ma);
bool qa_bms_over_temp_candidate(int32_t temp_c10);
bool qa_bms_sensor_fault_candidate(bool sensor_ready, int32_t shunt_ma, int32_t hall_ma);
bool qa_bms_charge_permit(uint16_t fault_bits);

#endif /* QA_BMS_ORACLE_H */
