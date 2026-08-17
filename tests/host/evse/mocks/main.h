#ifndef TEST_MOCK_MAIN_H_
#define TEST_MOCK_MAIN_H_

#include <stdint.h>

typedef struct
{
  uint32_t tag;
} GPIO_TypeDef;

typedef enum
{
  GPIO_PIN_RESET = 0,
  GPIO_PIN_SET
} GPIO_PinState;

extern GPIO_TypeDef g_gpioe;
extern GPIO_TypeDef g_gpiof;

/* Current product mapping used by MyApp/Hardware/hw_gpio.c */
#define RELAY_CTRL_GPIO_Port        (&g_gpioe)
#define RELAY_CTRL_Pin              ((uint16_t)(1U << 11))

#define RS485_DE_RE_GPIO_Port       (&g_gpioe)
#define RS485_DE_RE_Pin             ((uint16_t)(1U << 7))

#define START_BUTTON_GPIO_Port      (&g_gpioe)
#define START_BUTTON_Pin            ((uint16_t)(1U << 13))

#define STOP_BUTTON_GPIO_Port       (&g_gpiof)
#define STOP_BUTTON_Pin             ((uint16_t)(1U << 13))

#define CONNECTOR_DETECT_GPIO_Port  (&g_gpiof)
#define CONNECTOR_DETECT_Pin        ((uint16_t)(1U << 14))

#define ESTOP_INPUT_GPIO_Port       (&g_gpiof)
#define ESTOP_INPUT_Pin             ((uint16_t)(1U << 15))

void HAL_GPIO_WritePin(
    GPIO_TypeDef *port,
    uint16_t pin,
    GPIO_PinState state);

GPIO_PinState HAL_GPIO_ReadPin(
    GPIO_TypeDef *port,
    uint16_t pin);

#endif
