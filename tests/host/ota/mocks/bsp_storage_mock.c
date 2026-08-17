#include "bsp_storage_mock.h"

#include <stdbool.h>
#include <stddef.h>
#include <string.h>

#include "BSP/bsp_boot.h"
#include "BSP/bsp_storage.h"
#include "Common/boot_config.h"

/*
 * QA/QC note: this mock emulates flash constraints needed by the update
 * component.  It is deliberately independent from the product BSP so an
 * update algorithm defect cannot be hidden by reusing the same implementation.
 */
static uint8_t s_storage[BOOT_APP_MAX_SIZE];
static bool s_initialized;

static void set_error(bsp_storage_error_info_t *error_info,
                      bsp_storage_status_t status,
                      uint32_t address)
{
    if (error_info == NULL) {
        return;
    }
    memset(error_info, 0, sizeof(*error_info));
    error_info->status = status;
    error_info->address = address;
    error_info->sector = BSP_STORAGE_NO_SECTOR_ERROR;
}

void qa_storage_reset(void)
{
    memset(s_storage, 0xFF, sizeof(s_storage));
    s_initialized = false;
}

const uint8_t *qa_storage_data(void)
{
    return s_storage;
}

bsp_storage_status_t BspStorage_Init(void)
{
    s_initialized = true;
    return BSP_STORAGE_STATUS_OK;
}

bool BspStorage_IsInitialized(void)
{
    return s_initialized;
}

uint32_t BspStorage_GetApplicationStartAddress(void)
{
    return BOOT_APP_START_ADDRESS;
}

uint32_t BspStorage_GetApplicationCapacity(void)
{
    return BOOT_APP_MAX_SIZE;
}

bool BspStorage_IsImageSizeValid(uint32_t image_size)
{
    return (image_size > 0U) && (image_size <= BOOT_APP_MAX_SIZE);
}

bool BspStorage_IsRangeValid(uint32_t offset, uint32_t length)
{
    return (offset <= BOOT_APP_MAX_SIZE) &&
           (length <= (BOOT_APP_MAX_SIZE - offset));
}

bsp_storage_status_t BspStorage_EraseApplication(
    uint32_t image_size,
    bsp_storage_error_info_t *error_info)
{
    if (!s_initialized) {
        set_error(error_info, BSP_STORAGE_STATUS_NOT_INITIALIZED,
                  BOOT_APP_START_ADDRESS);
        return BSP_STORAGE_STATUS_NOT_INITIALIZED;
    }
    if (!BspStorage_IsImageSizeValid(image_size)) {
        set_error(error_info, BSP_STORAGE_STATUS_OUT_OF_RANGE,
                  BOOT_APP_START_ADDRESS);
        return BSP_STORAGE_STATUS_OUT_OF_RANGE;
    }
    memset(s_storage, 0xFF, image_size);
    set_error(error_info, BSP_STORAGE_STATUS_OK, BOOT_APP_START_ADDRESS);
    return BSP_STORAGE_STATUS_OK;
}

bsp_storage_status_t BspStorage_Write(
    uint32_t offset,
    const uint8_t *data,
    uint32_t length,
    bool final_chunk,
    bsp_storage_error_info_t *error_info)
{
    (void)final_chunk;
    if (!s_initialized) {
        set_error(error_info, BSP_STORAGE_STATUS_NOT_INITIALIZED,
                  BOOT_APP_START_ADDRESS + offset);
        return BSP_STORAGE_STATUS_NOT_INITIALIZED;
    }
    if ((data == NULL) || !BspStorage_IsRangeValid(offset, length)) {
        set_error(error_info, BSP_STORAGE_STATUS_INVALID_ARGUMENT,
                  BOOT_APP_START_ADDRESS + offset);
        return BSP_STORAGE_STATUS_INVALID_ARGUMENT;
    }
    for (uint32_t index = 0U; index < length; ++index) {
        if ((uint8_t)(s_storage[offset + index] & data[index]) != data[index]) {
            set_error(error_info, BSP_STORAGE_STATUS_NOT_ERASED,
                      BOOT_APP_START_ADDRESS + offset + index);
            return BSP_STORAGE_STATUS_NOT_ERASED;
        }
    }
    memcpy(&s_storage[offset], data, length);
    set_error(error_info, BSP_STORAGE_STATUS_OK,
              BOOT_APP_START_ADDRESS + offset);
    return BSP_STORAGE_STATUS_OK;
}

bsp_storage_status_t BspStorage_Verify(
    uint32_t offset,
    const uint8_t *data,
    uint32_t length,
    bsp_storage_error_info_t *error_info)
{
    if ((data == NULL) || !BspStorage_IsRangeValid(offset, length)) {
        set_error(error_info, BSP_STORAGE_STATUS_INVALID_ARGUMENT,
                  BOOT_APP_START_ADDRESS + offset);
        return BSP_STORAGE_STATUS_INVALID_ARGUMENT;
    }
    if (memcmp(&s_storage[offset], data, length) != 0) {
        set_error(error_info, BSP_STORAGE_STATUS_VERIFY_ERROR,
                  BOOT_APP_START_ADDRESS + offset);
        return BSP_STORAGE_STATUS_VERIFY_ERROR;
    }
    set_error(error_info, BSP_STORAGE_STATUS_OK,
              BOOT_APP_START_ADDRESS + offset);
    return BSP_STORAGE_STATUS_OK;
}

bool BspStorage_IsErased(uint32_t offset, uint32_t length)
{
    if (!BspStorage_IsRangeValid(offset, length)) {
        return false;
    }
    for (uint32_t index = 0U; index < length; ++index) {
        if (s_storage[offset + index] != 0xFFU) {
            return false;
        }
    }
    return true;
}

bool BspBoot_IsApplicationValid(void)
{
    uint32_t initial_msp;
    uint32_t reset_handler;
    memcpy(&initial_msp, &s_storage[0], sizeof(initial_msp));
    memcpy(&reset_handler, &s_storage[4], sizeof(reset_handler));
    return (initial_msp >= BOOT_SRAM_START_ADDRESS) &&
           (initial_msp <= BOOT_SRAM_STACK_TOP) &&
           ((reset_handler & 1U) != 0U) &&
           ((reset_handler & ~1UL) >= BOOT_APP_START_ADDRESS) &&
           ((reset_handler & ~1UL) < BOOT_APP_END_ADDRESS);
}
