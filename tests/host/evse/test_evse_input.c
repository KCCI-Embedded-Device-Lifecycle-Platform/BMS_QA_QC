#include <stdbool.h>
#include <stdio.h>

#include "app_config.h"
#include "evse_input.h"
#include "hw_gpio.h"
#include "qa_requirements.h"

#define CHECK(condition) do { if (!(condition)) { \
    fprintf(stderr, "%s:%d CHECK failed: %s\n", __FILE__, __LINE__, #condition); \
    return 1; \
} } while (0)

_Static_assert(EVSE_INPUT_DEBOUNCE_MS == QA_REQ_EVSE_DEBOUNCE_MS, "debounce drift");

int main(void)
{
    qa_gpio_set_connector(false);
    qa_gpio_set_estop(false);
    qa_gpio_set_start(false);
    qa_gpio_set_stop(false);
    evse_input_init();

    qa_gpio_set_start(true);
    evse_input_poll_10ms();
    evse_input_poll_10ms();
    CHECK(!evse_start_pressed_event());
    evse_input_poll_10ms();
    CHECK(evse_start_pressed_event());
    CHECK(!evse_start_pressed_event());

    qa_gpio_set_stop(true);
    evse_input_poll_10ms();
    evse_input_poll_10ms();
    CHECK(!evse_stop_pressed_event());
    evse_input_poll_10ms();
    CHECK(evse_stop_pressed_event());
    CHECK(!evse_stop_pressed_event());

    puts("PASS TC-EVSE-IN-001");
    return 0;
}
