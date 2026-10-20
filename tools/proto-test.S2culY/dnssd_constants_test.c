/* Verify derived dnssdint.h does NOT advertise RSA et/ek/am after exclusion. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "dnssdint.h"

int main(void) {
    /* RAOP_ET must be "0" (no RSA encryption type), not "0,1" */
    assert(strcmp(RAOP_ET, "0") == 0 &&
           "RAOP_ET still advertises RSA — et/ek must not include '1'");

    /* RAOP_EK must be "0" (no key), not "1" */
    assert(strcmp(RAOP_EK, "0") == 0 &&
           "RAOP_EK still set to 1 — RSA encryption key must not be advertised");

    /* GLOBAL_RAOP_MODEL must NOT be "AirPort4,107" — that routes senders to RSA path */
    assert(strstr(GLOBAL_RAOP_MODEL, "AirPort") == NULL &&
           "GLOBAL_RAOP_MODEL still AirPort4,107 — removes sender RSA routing");

    puts("dnssd_constants: 3 assertions passed — RAOP_ET=0, RAOP_EK=0, no AirPort model");
    return 0;
}
