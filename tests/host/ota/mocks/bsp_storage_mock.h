#ifndef QA_BSP_STORAGE_MOCK_H
#define QA_BSP_STORAGE_MOCK_H

#include <stdint.h>

void qa_storage_reset(void);
const uint8_t *qa_storage_data(void);

#endif /* QA_BSP_STORAGE_MOCK_H */
