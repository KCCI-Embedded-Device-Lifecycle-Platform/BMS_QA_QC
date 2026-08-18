#ifndef QA_MOCK_DBG_H
#define QA_MOCK_DBG_H

#include <stdio.h>

/*
 * Keep log output silent in Host tests while still compiling and type-checking
 * every format argument.  An empty variadic macro removes argument references
 * during preprocessing and incorrectly turns log-only product variables into
 * -Werror=unused-variable failures.
 *
 * The constant-false branch prevents runtime evaluation and side effects,
 * matching a disabled production log macro more closely than a sink function.
 */
#define QA_DBG_DISCARD(...)             \
    do {                                \
        if (0) {                        \
            (void)printf(__VA_ARGS__);  \
        }                               \
    } while (0)

#define DBG_E(...) QA_DBG_DISCARD(__VA_ARGS__)
#define DBG_W(...) QA_DBG_DISCARD(__VA_ARGS__)
#define DBG_I(...) QA_DBG_DISCARD(__VA_ARGS__)
#define DBG_D(...) QA_DBG_DISCARD(__VA_ARGS__)

#endif /* QA_MOCK_DBG_H */
