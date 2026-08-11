/*
 * TC-EVSE-REL-U002
 *
 * Host-side SWE.4 unit test for MyApp/Hardware/hw_gpio.c using a mocked HAL.
 * Verifies the relay active level and safe-output mapping without STM32 HW.
 */

#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include "hw_gpio.h"
#include "main.h"

GPIO_TypeDef g_gpioe = { .tag = 0xEEU };
GPIO_TypeDef g_gpiof = { .tag = 0xFFU };

typedef struct
{
  GPIO_TypeDef *port;
  uint16_t pin;
  GPIO_PinState state;
} gpio_write_t;

static gpio_write_t g_writes[16];
static unsigned int g_write_count;

void HAL_GPIO_WritePin(
    GPIO_TypeDef *port,
    uint16_t pin,
    GPIO_PinState state)
{
  if (g_write_count >= 16U)
  {
    fprintf(stderr, "FAIL: too many GPIO writes\n");
    exit(EXIT_FAILURE);
  }

  g_writes[g_write_count].port = port;
  g_writes[g_write_count].pin = pin;
  g_writes[g_write_count].state = state;
  g_write_count++;
}

GPIO_PinState HAL_GPIO_ReadPin(
    GPIO_TypeDef *port,
    uint16_t pin)
{
  (void)port;
  (void)pin;
  return GPIO_PIN_RESET;
}

static void fail(const char *message)
{
  fprintf(stderr, "FAIL: %s\n", message);
  exit(EXIT_FAILURE);
}

static void expect_write(
    unsigned int index,
    GPIO_TypeDef *expected_port,
    uint16_t expected_pin,
    GPIO_PinState expected_state,
    const char *message)
{
  if (index >= g_write_count)
    fail("expected GPIO write missing");

  if ((g_writes[index].port != expected_port) ||
      (g_writes[index].pin != expected_pin) ||
      (g_writes[index].state != expected_state))
  {
    fprintf(stderr,
            "FAIL: %s index=%u pin=0x%04X state=%d\n",
            message,
            index,
            g_writes[index].pin,
            (int)g_writes[index].state);
    exit(EXIT_FAILURE);
  }
}

int main(void)
{
  g_write_count = 0U;

  hw_gpio_relay_write(false);
  expect_write(
      0U,
      RELAY_CTRL_GPIO_Port,
      RELAY_CTRL_Pin,
      GPIO_PIN_RESET,
      "relay OFF must map to GPIO RESET");

  hw_gpio_relay_write(true);
  expect_write(
      1U,
      RELAY_CTRL_GPIO_Port,
      RELAY_CTRL_Pin,
      GPIO_PIN_SET,
      "relay ON request must map to GPIO SET");

  hw_gpio_apply_safe_outputs();

  expect_write(
      2U,
      RELAY_CTRL_GPIO_Port,
      RELAY_CTRL_Pin,
      GPIO_PIN_RESET,
      "safe outputs must force relay OFF first");

  expect_write(
      3U,
      RS485_DE_RE_GPIO_Port,
      RS485_DE_RE_Pin,
      GPIO_PIN_RESET,
      "safe outputs must force RS485 RX/disabled");

  if (g_write_count != 4U)
    fail("unexpected additional GPIO writes");

  puts("RESULT=PASS TC-EVSE-REL-U002");
  return EXIT_SUCCESS;
}
