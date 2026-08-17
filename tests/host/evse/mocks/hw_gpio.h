#ifndef QA_EVSE_MOCK_HW_GPIO_H
#define QA_EVSE_MOCK_HW_GPIO_H

#include <stdbool.h>

/*
 * Product-facing API mirrored from MyApp/Hardware/hw_gpio.h.
 *
 * This mock header intentionally shadows the STM32 product header so host
 * tests do not pull in HAL dependencies. Keep every function used by a host
 * harness declared here; otherwise -Werror correctly rejects an implicit
 * declaration before the product implementation is linked.
 */
void hw_gpio_apply_safe_outputs(void);
void hw_gpio_relay_write(bool on);
void hw_gpio_rs485_set_tx_mode(bool tx_mode);
void hw_gpio_status_led_write(bool on);
void hw_gpio_status_led_toggle(void);

bool hw_gpio_connector_is_connected(void);
bool hw_gpio_estop_is_active(void);
bool hw_gpio_start_button_is_pressed(void);
bool hw_gpio_stop_button_is_pressed(void);

void qa_gpio_set_connector(bool value);
void qa_gpio_set_estop(bool value);
void qa_gpio_set_start(bool value);
void qa_gpio_set_stop(bool value);

#endif /* QA_EVSE_MOCK_HW_GPIO_H */
