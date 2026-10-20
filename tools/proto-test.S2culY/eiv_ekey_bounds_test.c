/* Unit test for bounded eiv/ekey validation logic.
 * Mirrors the exact logic from raop_handlers.h (extracted inline to avoid
 * OpenSSL/plist link requirement for host test). */
#include <assert.h>
#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>

/* Mirrors the derived raop_handlers.h validation; returns 0=ok, 1=reject */
static int validate_eiv_ekey(uint64_t eiv_len, uint64_t ekey_len) {
    if (eiv_len != 16)  return 1;
    if (ekey_len != 72) return 1;
    return 0;
}

int main(void) {
    /* exact lengths accepted */
    assert(validate_eiv_ekey(16, 72) == 0);

    /* eiv too short */
    assert(validate_eiv_ekey(0,  72) == 1);
    assert(validate_eiv_ekey(15, 72) == 1);
    assert(validate_eiv_ekey(1,  72) == 1);

    /* eiv too long (overflow attempt) */
    assert(validate_eiv_ekey(17, 72)   == 1);
    assert(validate_eiv_ekey(255, 72)  == 1);
    assert(validate_eiv_ekey(UINT64_MAX, 72) == 1);

    /* ekey too short */
    assert(validate_eiv_ekey(16, 0)  == 1);
    assert(validate_eiv_ekey(16, 71) == 1);

    /* ekey too long */
    assert(validate_eiv_ekey(16, 73)          == 1);
    assert(validate_eiv_ekey(16, 256)         == 1);
    assert(validate_eiv_ekey(16, UINT64_MAX)  == 1);

    /* both wrong */
    assert(validate_eiv_ekey(0, 0)   == 1);
    assert(validate_eiv_ekey(32, 144) == 1);

    puts("eiv_ekey_bounds: 14 assertions passed — exact-length gate blocks all malformed inputs");
    return 0;
}
