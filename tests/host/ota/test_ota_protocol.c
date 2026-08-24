#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "Middleware/boot_protocol.h"

#define CHECK(condition) do { if (!(condition)) { \
    fprintf(stderr, "%s:%d CHECK failed: %s\n", __FILE__, __LINE__, #condition); \
    return 1; \
} } while (0)

static int run_protocol_round_trip(void)
{
    boot_protocol_packet_t input = {0};
    boot_protocol_packet_t output = {0};
    boot_protocol_parser_t parser;
    uint8_t frame[BOOT_PROTOCOL_MAX_FRAME_SIZE];
    uint16_t frame_length = 0U;
    boot_protocol_result_t result = BOOT_PROTOCOL_RESULT_NONE;

    input.command = BOOT_PROTOCOL_CMD_HELLO;
    input.length = 3U;
    input.data[0] = 0x10U;
    input.data[1] = 0x20U;
    input.data[2] = 0x30U;
    CHECK(BootProtocol_Encode(&input, frame, sizeof(frame), &frame_length) == MW_STATUS_OK);
    CHECK(frame[0] == BOOT_PROTOCOL_SOF_1);
    CHECK(frame[1] == BOOT_PROTOCOL_SOF_2);
    CHECK(frame[3] == 3U && frame[4] == 0U); /* length is little-endian */

    BootProtocol_Init(&parser);
    for (uint16_t index = 0U; index < frame_length; ++index) {
        result = BootProtocol_ProcessByte(&parser, frame[index], &output);
    }
    CHECK(result == BOOT_PROTOCOL_RESULT_PACKET_READY);
    CHECK(output.command == input.command);
    CHECK(output.length == input.length);
    CHECK(memcmp(output.data, input.data, input.length) == 0);
    puts("PASS TC-OTA-PROTO-001");
    return 0;
}

static int run_crc_reject(void)
{
    boot_protocol_packet_t input = {0};
    boot_protocol_packet_t output = {0};
    boot_protocol_parser_t parser;
    uint8_t frame[BOOT_PROTOCOL_MAX_FRAME_SIZE];
    uint16_t frame_length = 0U;
    boot_protocol_result_t result = BOOT_PROTOCOL_RESULT_NONE;

    input.command = BOOT_PROTOCOL_CMD_DATA;
    input.length = 4U;
    input.data[0] = 1U;
    input.data[1] = 2U;
    input.data[2] = 3U;
    input.data[3] = 4U;
    CHECK(BootProtocol_Encode(&input, frame, sizeof(frame), &frame_length) == MW_STATUS_OK);
    frame[frame_length - 1U] ^= 0x80U;

    BootProtocol_Init(&parser);
    memset(&output, 0xA5, sizeof(output));
    for (uint16_t index = 0U; index < frame_length; ++index) {
        result = BootProtocol_ProcessByte(&parser, frame[index], &output);
    }
    CHECK(result == BOOT_PROTOCOL_RESULT_CRC_ERROR);
    puts("PASS TC-OTA-PROTO-002");
    return 0;
}

int main(int argc, char **argv)
{
    if (argc != 2) {
        return 2;
    }
    if (strcmp(argv[1], "TC-OTA-PROTO-001") == 0) {
        return run_protocol_round_trip();
    }
    if (strcmp(argv[1], "TC-OTA-PROTO-002") == 0) {
        return run_crc_reject();
    }
    return 2;
}
