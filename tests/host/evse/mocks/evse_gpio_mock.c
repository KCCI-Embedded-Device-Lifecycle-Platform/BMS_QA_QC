#include "hw_gpio.h"

static bool s_connector;
static bool s_estop;
static bool s_start;
static bool s_stop;

bool hw_gpio_connector_is_connected(void) { return s_connector; }
bool hw_gpio_estop_is_active(void) { return s_estop; }
bool hw_gpio_start_button_is_pressed(void) { return s_start; }
bool hw_gpio_stop_button_is_pressed(void) { return s_stop; }

void qa_gpio_set_connector(bool value) { s_connector = value; }
void qa_gpio_set_estop(bool value) { s_estop = value; }
void qa_gpio_set_start(bool value) { s_start = value; }
void qa_gpio_set_stop(bool value) { s_stop = value; }
