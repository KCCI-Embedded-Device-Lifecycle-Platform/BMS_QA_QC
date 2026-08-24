#ifndef QA_REQUIREMENTS_H
#define QA_REQUIREMENTS_H

#include <stdint.h>

/* Approved requirement baseline. Do not derive these values from product headers. */
#define QA_REQ_BMS_CELL_OV_MV             4200
#define QA_REQ_BMS_CELL_OV_CLEAR_MV       4150
#define QA_REQ_BMS_CELL_UV_MV             3000
#define QA_REQ_BMS_CELL_UV_CLEAR_MV       3100
#define QA_REQ_BMS_PACK_OV_MV            16800
#define QA_REQ_BMS_PACK_OV_CLEAR_MV      16600
#define QA_REQ_BMS_OVER_CURRENT_MA        1000
#define QA_REQ_BMS_OVER_TEMP_C10           550
#define QA_REQ_BMS_OVER_TEMP_CLEAR_C10     500
#define QA_REQ_BMS_SENSOR_DIFF_MA           500
#define QA_REQ_BMS_FAULT_CONFIRM_COUNT        3U
#define QA_REQ_BMS_FAULT_TASK_MS             100U
#define QA_REQ_BMS_FAULT_CLEAR_HOLD_MS      3000U
#define QA_REQ_BMS_LINK_TIMEOUT_MS          1000U
#define QA_REQ_BMS_LINK_CLEAR_HOLD_MS        300U

#define QA_REQ_EVSE_DEBOUNCE_MS               30U
#define QA_REQ_EVSE_BMS_TIMEOUT_MS            500U

#define QA_REQ_CAN_BITRATE_BPS              500000U
#define QA_REQ_CAN_ID_BMS_MAIN              0x100U
#define QA_REQ_CAN_ID_BMS_CELL              0x101U
#define QA_REQ_CAN_ID_BMS_TEMP              0x102U
#define QA_REQ_CAN_ID_BMS_STATE             0x103U
#define QA_REQ_CAN_ID_BMS_VERSION           0x104U
#define QA_REQ_CAN_ID_BMS_RESPONSE          0x105U
#define QA_REQ_CAN_ID_EVSE_STATUS           0x200U
#define QA_REQ_CAN_ID_EVSE_REQUEST          0x201U
#define QA_REQ_CAN_ID_EVSE_FAULT            0x202U
#define QA_REQ_CAN_ID_OTA_ENTER             0x203U
#define QA_REQ_CAN_ID_OTA_DATA              0x204U
#define QA_REQ_CAN_ID_PARAM_WRITE           0x205U

#define QA_REQ_CAN_DLC_BMS_MAIN                  8U
#define QA_REQ_CAN_DLC_BMS_CELL                  8U
#define QA_REQ_CAN_DLC_BMS_TEMP                  8U
#define QA_REQ_CAN_DLC_BMS_STATE                 2U
#define QA_REQ_CAN_DLC_BMS_VERSION               4U
#define QA_REQ_CAN_DLC_BMS_RESPONSE              4U
#define QA_REQ_CAN_DLC_EVSE_STATUS               4U
#define QA_REQ_CAN_DLC_EVSE_REQUEST              1U
#define QA_REQ_CAN_DLC_EVSE_FAULT                1U
#define QA_REQ_CAN_DLC_OTA_ENTER                 0U
#define QA_REQ_CAN_DLC_PARAM_WRITE               4U

#define QA_REQ_BMS_FAULT_CRITICAL_MASK          0x7FU
#define QA_REQ_OTA_APP_START_ADDRESS      0x08020000UL
#define QA_REQ_OTA_APP_END_ADDRESS        0x08100000UL
#define QA_REQ_OTA_APP_CAPACITY \
    (QA_REQ_OTA_APP_END_ADDRESS - QA_REQ_OTA_APP_START_ADDRESS)

#endif /* QA_REQUIREMENTS_H */
