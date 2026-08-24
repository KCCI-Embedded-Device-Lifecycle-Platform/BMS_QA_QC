#ifndef QA_OTA_ORACLE_H
#define QA_OTA_ORACLE_H

#include <stdbool.h>
#include <stdint.h>

bool qa_ota_image_size_valid(uint32_t image_size, uint32_t capacity);
bool qa_ota_chunk_valid(uint32_t expected_offset,
                        uint32_t received_offset,
                        uint32_t chunk_length,
                        uint32_t image_size);

#endif /* QA_OTA_ORACLE_H */
