#ifndef QA_EVSE_MOCK_HW_GPIO_H
#define QA_EVSE_MOCK_HW_GPIO_H

#include <stdbool.h>

bool hw_gpio_connector_is_connected(void);
bool hw_gpio_estop_is_active(void);
bool hw_gpio_start_button_is_pressed(void);
bool hw_gpio_stop_button_is_pressed(void);

void qa_gpio_set_connector(bool value);
void qa_gpio_set_estop(bool value);
void qa_gpio_set_start(bool value);
void qa_gpio_set_stop(bool value);

#endif /* QA_EVSE_MOCK_HW_GPIO_H */
