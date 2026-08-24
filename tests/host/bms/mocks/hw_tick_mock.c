#include "hw_tick.h"

static uint32_t s_now_ms;

void qa_tick_set(uint32_t now_ms)
{
    s_now_ms = now_ms;
}

void qa_tick_advance(uint32_t delta_ms)
{
    s_now_ms += delta_ms;
}

uint32_t hw_tick_ms(void)
{
    return s_now_ms;
}

void hw_tick_delay(uint32_t ms)
{
    s_now_ms += ms;
}

bool hw_tick_due(uint32_t *last, uint32_t period)
{
    if ((uint32_t)(s_now_ms - *last) < period) {
        return false;
    }
    *last = s_now_ms;
    return true;
}

bool hw_tick_elapsed(uint32_t start, uint32_t period)
{
    return (uint32_t)(s_now_ms - start) >= period;
}
