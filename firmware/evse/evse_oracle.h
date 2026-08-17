#ifndef QA_EVSE_ORACLE_H
#define QA_EVSE_ORACLE_H

#include <stdbool.h>
#include <stdint.h>

typedef struct {
    bool connector_connected;
    bool bms_online;
    bool charge_permit;
    bool estop_active;
    uint32_t fault_bits;
    bool ota_requested;
} qa_evse_charge_conditions_t;

bool qa_evse_charge_allowed(const qa_evse_charge_conditions_t *conditions);
bool qa_evse_bms_timed_out(uint32_t now_ms, uint32_t last_bms_main_ms);

#endif /* QA_EVSE_ORACLE_H */
