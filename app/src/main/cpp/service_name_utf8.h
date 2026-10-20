#ifndef PAD_SERVICE_NAME_UTF8_H
#define PAD_SERVICE_NAME_UTF8_H
#include <stddef.h>
#include <stdint.h>
/* Convert Java UTF-16 code units to DNS's standard UTF-8, never JNI modified
 * UTF-8. Fail closed on malformed surrogates, embedded NUL or a byte budget
 * overflow. The caller reserves the RAOP prefix; no truncation occurs here. */
static int service_name_utf8(const uint16_t *input, size_t length, char *out, size_t capacity) {
    size_t used = 0;
    if (!input || !out || !length || !capacity) return -1;
    for (size_t i = 0; i < length; i++) {
        uint32_t cp = input[i];
        if (cp >= 0xd800 && cp <= 0xdbff) {
            if (++i >= length || input[i] < 0xdc00 || input[i] > 0xdfff) return -1;
            cp = 0x10000 + ((cp - 0xd800) << 10) + (input[i] - 0xdc00);
        } else if (cp >= 0xdc00 && cp <= 0xdfff) return -1;
        if (!cp) return -1;
        size_t bytes = cp < 0x80 ? 1 : cp < 0x800 ? 2 : cp < 0x10000 ? 3 : 4;
        if (bytes >= capacity || used >= capacity - bytes) return -1;
        if (bytes == 1) out[used++] = (char)cp;
        else {
            if (bytes == 4) out[used++] = (char)(0xf0 | (cp >> 18));
            if (bytes >= 3) out[used++] = (char)((bytes == 3 ? 0xe0 : 0x80) | ((cp >> 12) & 0x3f));
            out[used++] = (char)((bytes == 2 ? 0xc0 : 0x80) | ((cp >> 6) & (bytes == 2 ? 0x1f : 0x3f)));
            out[used++] = (char)(0x80 | (cp & 0x3f));
        }
    }
    out[used] = 0;
    return (int)used;
}
#endif
