#ifndef QA_HW_TICK_MOCK_H
#define QA_HW_TICK_MOCK_H

#include <stdint.h>

void qa_tick_set(uint32_t now_ms);
void qa_tick_advance(uint32_t delta_ms);

#endif /* QA_HW_TICK_MOCK_H */
