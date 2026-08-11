/*
 * TC-EVSE-REL-U001
 *
 * Host-side SWE.4 unit test for the current EVSE relay driver baseline.
 * Product source under test: MyApp/Driver/relay.c
 *
 * Current app_config.h intentionally has:
 *   EVSE_CFG_RELAY_ACTUATION_ENABLED = 0U
 *
 * Therefore every ON request must remain physically commanded OFF.
 */

#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>

#include "relay.h"

static bool g_last_hw_on;
static unsigned int g_hw_write_count;

void hw_gpio_relay_write(bool on)
{
  g_last_hw_on = on;
  g_hw_write_count++;
}

static void fail(const char *message)
{
  fprintf(stderr, "FAIL: %s\n", message);
  exit(EXIT_FAILURE);
}

static void expect_false(bool value, const char *message)
{
  if (value)
  {
    fail(message);
  }
}

static void expect_count(unsigned int expected, const char *message)
{
  if (g_hw_write_count != expected)
  {
    fprintf(stderr,
            "FAIL: %s expected=%u actual=%u\n",
            message,
            expected,
            g_hw_write_count);
    exit(EXIT_FAILURE);
  }
}

int main(void)
{
  bool accepted;

  g_last_hw_on = true;
  g_hw_write_count = 0U;

  relay_init();
  expect_count(1U, "relay_init must issue one hardware write");
  expect_false(g_last_hw_on, "relay_init must drive Safe-Off");
  expect_false(relay_get_command(), "relay command after init must be OFF");

  accepted = relay_request_on();
  expect_false(accepted,
               "ON request must be rejected while actuation is disabled");
  expect_false(g_last_hw_on,
               "rejected ON request must keep hardware command OFF");
  expect_false(relay_get_command(),
               "rejected ON request must keep software command OFF");

  relay_set(true);
  expect_false(g_last_hw_on,
               "relay_set(true) must remain OFF in bench-safe build");
  expect_false(relay_get_command(),
               "relay_set(true) command state must remain OFF");

  relay_set(false);
  expect_false(g_last_hw_on, "relay_set(false) must drive OFF");
  expect_false(relay_get_command(), "relay_set(false) command must be OFF");

  relay_force_off();
  expect_false(g_last_hw_on, "relay_force_off must drive OFF");
  expect_false(relay_get_command(), "relay_force_off command must be OFF");

  puts("RESULT=PASS TC-EVSE-REL-U001");
  return EXIT_SUCCESS;

}