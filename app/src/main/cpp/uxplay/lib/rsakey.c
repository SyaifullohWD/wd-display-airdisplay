/*
 * rsakey.c — stub: legacy RAOP/AirTunes RSA key is excluded from this build.
 *
 * The donor rsakey.c contains the "widely published AirPort Express private key"
 * used only for legacy RAOP audio (iTunes / AirTunes ANNOUNCE path).  That code
 * is NOT part of the screen-mirroring call path and is physically excluded from
 * the Pocket AirDisplay derived source tree.
 *
 * All callers in raop.c and raop_handlers.h already guard on rsakey_init()
 * returning NULL (see raop.c:730 and raop_handlers.h:662), so the legacy RAOP
 * ANNOUNCE path is disabled at runtime when this stub is in use.
 *
 * This file is part of the Pocket AirDisplay project (GPLv3).
 */

#include "rsakey.h"

rsakey_t *rsakey_init(void) { return NULL; }
void rsakey_destroy(rsakey_t *rsakey) { (void)rsakey; }

char *rsakey_sign_challenge(rsakey_t *rsakey, const char *challenge_b64,
                            const unsigned char *local_addr, int local_addr_len,
                            const unsigned char *hwaddr, int hwaddr_len) {
    (void)rsakey; (void)challenge_b64;
    (void)local_addr; (void)local_addr_len;
    (void)hwaddr; (void)hwaddr_len;
    return NULL;
}

int rsakey_decrypt_aeskey(rsakey_t *rsakey, const char *rsaaeskey_b64,
                          unsigned char aeskey[16]) {
    (void)rsakey; (void)rsaaeskey_b64; (void)aeskey;
    return -1;
}

unsigned char *rsakey_base64_decode(const char *input, int *outlen) {
    (void)input;
    if (outlen) *outlen = 0;
    return NULL;
}

char *rsakey_base64_encode(const unsigned char *input, int inlen) {
    (void)input; (void)inlen;
    return NULL;
}
