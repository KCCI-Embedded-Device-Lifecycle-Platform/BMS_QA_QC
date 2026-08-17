#include "ota_oracle.h"

bool qa_ota_image_size_valid(uint32_t image_size, uint32_t capacity)
{
    return image_size >= 8U && image_size <= capacity;
}

bool qa_ota_chunk_valid(uint32_t expected_offset,
                        uint32_t received_offset,
                        uint32_t chunk_length,
                        uint32_t image_size)
{
    if (received_offset != expected_offset || chunk_length == 0U) {
        return false;
    }
    if (received_offset >= image_size) {
        return false;
    }
    return chunk_length <= (image_size - received_offset);
}
