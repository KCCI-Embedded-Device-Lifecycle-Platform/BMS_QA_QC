#include "evse_oracle.h"

#include "qa_requirements.h"

bool qa_evse_charge_allowed(const qa_evse_charge_conditions_t *conditions)
{
    if (conditions == 0) {
        return false;
    }

    return conditions->connector_connected &&
           conditions->bms_online &&
           conditions->charge_permit &&
           !conditions->estop_active &&
           conditions->fault_bits == 0U &&
           !conditions->ota_requested;
}

bool qa_evse_bms_timed_out(uint32_t now_ms, uint32_t last_bms_main_ms)
{
    return (uint32_t)(now_ms - last_bms_main_ms) > QA_REQ_EVSE_BMS_TIMEOUT_MS;
}
