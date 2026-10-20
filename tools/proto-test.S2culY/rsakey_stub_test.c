/* rsakey_stub_test: verifies derived rsakey.c (no key, all stubs return NULL/error).
 * Links only our derived rsakey.c + rsakey.h — no OpenSSL needed. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "rsakey.h"

int main(void) {
    /* init must return NULL so callers know legacy path is disabled */
    rsakey_t *key = rsakey_init();
    assert(key == NULL);

    /* destroy must accept NULL without crash */
    rsakey_destroy(NULL);
    rsakey_destroy(key); /* also NULL */

    /* sign_challenge with NULL key returns NULL */
    unsigned char addr[4] = {127,0,0,1};
    unsigned char hw[6] = {0};
    char *resp = rsakey_sign_challenge(NULL, "dGVzdA==", addr, 4, hw, 6);
    assert(resp == NULL);

    /* decrypt_aeskey with NULL key returns -1 */
    unsigned char aeskey[16] = {0};
    int rc = rsakey_decrypt_aeskey(NULL, "dGVzdA==", aeskey);
    assert(rc == -1);

    /* base64 helpers return NULL */
    int outlen = 99;
    unsigned char *dec = rsakey_base64_decode("dGVzdA==", &outlen);
    assert(dec == NULL);
    assert(outlen == 0);
    char *enc = rsakey_base64_encode((unsigned char *)"test", 4);
    assert(enc == NULL);

    puts("rsakey_stub: 7 assertions passed — NULL init, NULL-safe destroy, all stubs inert");
    return 0;
}
