#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "App/ap_boot_update.h"
#include "App/ap_boot_command.h"
#include "BSP/bsp_storage.h"
#include "Common/boot_config.h"
#include "Middleware/boot_crc32.h"
#include "bsp_storage_mock.h"
#include "ota_oracle.h"
#include "qa_requirements.h"

#define CHECK(condition) do { if (!(condition)) { \
    fprintf(stderr, "%s:%d CHECK failed: %s\n", __FILE__, __LINE__, #condition); \
    return 1; \
} } while (0)

_Static_assert(BOOT_APP_START_ADDRESS == QA_REQ_OTA_APP_START_ADDRESS,
               "app start drift");
_Static_assert(BOOT_APP_MAX_SIZE == QA_REQ_OTA_APP_CAPACITY, "capacity drift");

static void make_valid_image(uint8_t image[16])
{
    const uint32_t msp = 0x20001000UL;
    const uint32_t reset = BOOT_APP_START_ADDRESS + 9UL;
    memset(image, 0x5A, 16U);
    memcpy(&image[0], &msp, sizeof(msp));
    memcpy(&image[4], &reset, sizeof(reset));
}

static int initialize(ap_boot_update_context_t *context)
{
    qa_storage_reset();
    CHECK(BspStorage_Init() == BSP_STORAGE_STATUS_OK);
    CHECK(ApBootUpdate_Init(context));
    return 0;
}

static int run_size(void)
{
    ap_boot_update_context_t context;
    CHECK(initialize(&context) == 0);
    CHECK(!ApBootUpdate_Start(&context, 0U, 0U));
    CHECK(ApBootUpdate_GetLastError(&context) == AP_BOOT_UPDATE_ERROR_INVALID_IMAGE_SIZE);
    ApBootUpdate_Abort(&context);
    CHECK(!ApBootUpdate_Start(&context, AP_BOOT_UPDATE_VECTOR_TABLE_SIZE - 1U, 0U));
    CHECK(ApBootUpdate_GetLastError(&context) == AP_BOOT_UPDATE_ERROR_INVALID_IMAGE_SIZE);
    ApBootUpdate_Abort(&context);
    CHECK(!ApBootUpdate_Start(&context, QA_REQ_OTA_APP_CAPACITY + 1U, 0U));
    CHECK(ApBootUpdate_GetLastError(&context) == AP_BOOT_UPDATE_ERROR_INVALID_IMAGE_SIZE);
    CHECK(!qa_ota_image_size_valid(0U, QA_REQ_OTA_APP_CAPACITY));
    CHECK(qa_ota_image_size_valid(QA_REQ_OTA_APP_CAPACITY,
                                  QA_REQ_OTA_APP_CAPACITY));
    CHECK(!qa_ota_image_size_valid(QA_REQ_OTA_APP_CAPACITY + 1U,
                                   QA_REQ_OTA_APP_CAPACITY));
    puts("PASS TC-OTA-SIZE-001");
    return 0;
}

static int run_offset(void)
{
    ap_boot_update_context_t context;
    uint8_t image[16];
    make_valid_image(image);
    CHECK(initialize(&context) == 0);
    CHECK(ApBootUpdate_Start(&context, sizeof(image), 0U));
    CHECK(!ApBootUpdate_WriteData(&context, 4U, image, 4U));
    CHECK(ApBootUpdate_GetLastError(&context) == AP_BOOT_UPDATE_ERROR_INVALID_OFFSET);
    CHECK(!qa_ota_chunk_valid(0U, 4U, 4U, 16U));
    puts("PASS TC-OTA-OFFSET-001");
    return 0;
}

static int run_crc_reject(void)
{
    ap_boot_update_context_t context;
    uint8_t image[16];
    uint32_t expected_crc = 0U;
    make_valid_image(image);
    CHECK(BootCrc32_Calculate(image, sizeof(image), &expected_crc) == MW_STATUS_OK);
    CHECK(initialize(&context) == 0);
    CHECK(ApBootUpdate_Start(&context, sizeof(image), expected_crc ^ 1UL));
    CHECK(ApBootUpdate_WriteData(&context, 0U, image, sizeof(image)));
    CHECK(!ApBootUpdate_End(&context));
    CHECK(ApBootUpdate_GetLastError(&context) == AP_BOOT_UPDATE_ERROR_CRC_MISMATCH);
    CHECK(qa_storage_data()[0] == 0xFFU); /* invalid image never becomes bootable */
    puts("PASS TC-OTA-CRC-001");
    return 0;
}

static int run_valid_update(void)
{
    ap_boot_update_context_t context;
    uint8_t image[16];
    uint32_t expected_crc = 0U;
    make_valid_image(image);
    CHECK(BootCrc32_Calculate(image, sizeof(image), &expected_crc) == MW_STATUS_OK);
    CHECK(initialize(&context) == 0);
    CHECK(ApBootUpdate_Start(&context, sizeof(image), expected_crc));
    CHECK(qa_storage_data()[0] == 0xFFU); /* vector held back */
    CHECK(ApBootUpdate_WriteData(&context, 0U, image, 8U));
    CHECK(ApBootUpdate_WriteData(&context, 8U, &image[8], 8U));
    CHECK(ApBootUpdate_End(&context));
    CHECK(ApBootUpdate_GetState(&context) == AP_BOOT_UPDATE_STATE_COMPLETE);
    CHECK(memcmp(qa_storage_data(), image, sizeof(image)) == 0);
    puts("PASS TC-OTA-UPDATE-001 host-component");
    return 0;
}

static int run_text_protocol(void)
{
    ap_boot_text_command_result_t result;
    CHECK(ApBootCommand_ProcessText("HELLO", &result));
    CHECK(result.action == AP_BOOT_ACTION_NONE);
    CHECK(strcmp(result.response, "[BOOT] ACK\r\n") == 0);
    CHECK(ApBootCommand_ProcessText("VERSION", &result));
    CHECK(strncmp(result.response, "[BOOT] VERSION ", 15U) == 0);
    CHECK(ApBootCommand_ProcessText("PROTO", &result));
    CHECK(result.action == AP_BOOT_ACTION_ENTER_BINARY_PROTOCOL);
    CHECK(ApBootCommand_ProcessText("RUN", &result));
    CHECK(result.action == AP_BOOT_ACTION_RUN_APPLICATION);
    CHECK(result.response == NULL);
    CHECK(ApBootCommand_ProcessText("UNKNOWN", &result));
    CHECK(strcmp(result.response, "[BOOT] NACK\r\n") == 0);
    puts("PASS TC-OTA-PROTO-001 text-command");
    return 0;
}

int main(int argc, char **argv)
{
    if (argc != 2) {
        return 2;
    }
    if (strcmp(argv[1], "TC-OTA-SIZE-001") == 0) return run_size();
    if (strcmp(argv[1], "TC-OTA-OFFSET-001") == 0) return run_offset();
    if (strcmp(argv[1], "TC-OTA-CRC-001") == 0) return run_crc_reject();
    if (strcmp(argv[1], "TC-OTA-UPDATE-001") == 0) return run_valid_update();
    if (strcmp(argv[1], "TC-OTA-PROTO-001") == 0) return run_text_protocol();
    return 2;
}
