/*
 * core_protocol_test.c — host-native production handler + discovery test.
 *
 * Architecture: unity-build approach.
 *   - http_response.c / http_request.c / rsakey.c / dnssd.c / dnssd_mdnsd.c
 *     / raop.c  are all #included into THIS translation unit so the static
 *     handler functions in raop_handlers.h become callable from tests here.
 *   - All networking (raop_ntp, raop_rtp, raop_rtp_mirror, httpd, mdnsd
 *     sockets) is stubbed — no LAN traffic is emitted.
 *   - Real host libplist-2.0 and libcrypto used for plist + crypto.
 *   - Real logger / utils / byteutils / compat / netutils / crypto / srp /
 *     pairing are compiled separately (see build script).
 *
 * Build: scripts/test-core-protocol.sh
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <assert.h>
#include <strings.h>   /* strncasecmp */

/* =========================================================
 * 0.  OPAQUE STRUCT DEFINITIONS for types whose .c files
 *     we are NOT compiling.  Must precede ANY #include
 *     that exposes the opaque typedef so the compiler
 *     never sees an incomplete type where we need a size.
 * ========================================================= */
struct raop_ntp_s       { int _s; };
struct raop_rtp_s       { int _s; };
struct raop_rtp_mirror_s{ int _s; };
struct httpd_s          { int _s; };
struct fairplay_s       { int _s; };
struct airplay_video_s  { int _s; };
struct mirror_buffer_s  { int _s; };
struct mdnsd_s          { int _s; };

/* =========================================================
 * 1.  UNITY BUILDS — order matters for include dependencies.
 *     All stubs live AFTER these includes; non-static calls
 *     from the unity-built code resolve via the linker even
 *     within a single TU.
 * ========================================================= */
#include "http_response.c"   /* gives us struct http_response_s */
#include "http_request.c"    /* gives us struct http_request_s  */
#include "rsakey.c"          /* no-op stub already in tree      */
#include "dnssd.c"
#include "mdnsd/dnssd_mdnsd.c"
#include "raop.c"            /* also pulls in raop_handlers.h + http_handlers.h */

/* =========================================================
 * 2.  STUB IMPLEMENTATIONS
 *     Placed after unity-builds so raop_callbacks_t and all
 *     other types are fully defined when we reference them.
 * ========================================================= */

/* Test control globals — set by individual tests */
int g_ntp_init_fail = 0;   /* 1 → raop_ntp_init returns NULL */

/* ---------- httpd ---------- */
httpd_t *httpd_init(logger_t *logger, httpd_callbacks_t *cbs, int nohold) {
    (void)logger; (void)cbs; (void)nohold;
    return calloc(1, sizeof(httpd_t));
}
int httpd_start(httpd_t *h, unsigned short *port) {
    (void)h; (void)port; return 0;
}
void httpd_stop(httpd_t *h)    { (void)h; }
void httpd_destroy(httpd_t *h) { free(h); }
void *httpd_get_connection_by_type(httpd_t *h, connection_type_t t, int create) {
    (void)h; (void)t; (void)create; return NULL;
}

/* ---------- raop_ntp ---------- */
raop_ntp_t *raop_ntp_init(logger_t *logger, raop_callbacks_t *cbs,
                           const char *remote, int remotelen,
                           unsigned short timing_rport,
                           timing_protocol_t *proto) {
    (void)logger; (void)cbs; (void)remote; (void)remotelen;
    (void)timing_rport; (void)proto;
    if (g_ntp_init_fail) return NULL;
    return calloc(1, sizeof(raop_ntp_t));
}
void raop_ntp_start(raop_ntp_t *n, unsigned short *p) { (void)n; (void)p; }
void raop_ntp_stop(raop_ntp_t *n)    { (void)n; }
void raop_ntp_destroy(raop_ntp_t *n) { free(n); }
uint64_t raop_ntp_get_local_time(void) { return 0; }
/* get_local_time and ntp_global_init are defined in raop.c (unity-built above) */
uint64_t raop_ntp_get_remote_time(raop_ntp_t *n) { (void)n; return 0; }
uint64_t raop_ntp_convert_remote_time(raop_ntp_t *n, uint64_t t) { (void)n; return t; }
uint64_t raop_ntp_convert_local_time(raop_ntp_t *n, uint64_t t)  { (void)n; return t; }
uint64_t raop_ntp_timestamp_to_nano_seconds(uint64_t ts, bool b)  { (void)b; return ts; }
uint64_t raop_remote_timestamp_to_nano_seconds(raop_ntp_t *n, uint64_t ts) { (void)n; return ts; }
unsigned short raop_ntp_get_port(raop_ntp_t *n) { (void)n; return 0; }
void raop_ntp_set_video_arrival_offset(raop_ntp_t *n, const uint64_t *o) { (void)n; (void)o; }
uint64_t raop_ntp_get_video_arrival_offset(raop_ntp_t *n) { (void)n; return 0; }
void raop_ntp_global_init(void) {}
kernel_timestamp_session_t *kernel_timestamp_session_create(int fd) { (void)fd; return NULL; }
ssize_t kernel_timestamp_session_recv(kernel_timestamp_session_t *s, char *b,
                                      size_t l, uint64_t *us, void *src, int *len) {
    (void)s; (void)b; (void)l; (void)us; (void)src; (void)len; return -1;
}
void kernel_timestamp_session_destroy(kernel_timestamp_session_t *s) { free(s); }
void *raop_ntp_thread_worker(void *p) { (void)p; return NULL; }

/* ---------- raop_rtp ---------- */
raop_rtp_t *raop_rtp_init(logger_t *logger, raop_callbacks_t *cbs,
                           raop_ntp_t *ntp, const char *remote, int remotelen,
                           const unsigned char *aeskey, const unsigned char *aesiv) {
    (void)logger; (void)cbs; (void)ntp; (void)remote; (void)remotelen;
    (void)aeskey; (void)aesiv;
    return calloc(1, sizeof(raop_rtp_t));
}
void raop_rtp_destroy(raop_rtp_t *r) { free(r); }
void raop_rtp_remote_control_id(raop_rtp_t *r, const char *d, const char *a) {
    (void)r; (void)d; (void)a;
}
void raop_rtp_start(raop_rtp_t *r, int n, unsigned short *d,
                    unsigned short *c, unsigned short *t) {
    (void)r; (void)n; (void)d; (void)c; (void)t;
}
void raop_rtp_stop(raop_rtp_t *r) { (void)r; }

/* ---------- raop_rtp_mirror ---------- */
raop_rtp_mirror_t *raop_rtp_mirror_init(logger_t *logger, raop_callbacks_t *cbs,
                                         raop_ntp_t *ntp, const char *remote,
                                         int remotelen, const unsigned char *aeskey) {
    (void)logger; (void)cbs; (void)ntp; (void)remote; (void)remotelen; (void)aeskey;
    return calloc(1, sizeof(raop_rtp_mirror_t));
}
int raop_rtp_mirror_init_aes(raop_rtp_mirror_t *m, uint64_t *id) { (void)m; (void)id; return 0; }
void raop_rtp_mirror_start(raop_rtp_mirror_t *m, unsigned short *p, uint8_t fps) {
    (void)m; (void)p; (void)fps;
}
void raop_rtp_mirror_stop(raop_rtp_mirror_t *m)    { (void)m; }
void raop_rtp_mirror_destroy(raop_rtp_mirror_t *m) { free(m); }

/* ---------- fairplay ---------- */
fairplay_t *fairplay_init(logger_t *logger) {
    (void)logger;
    return calloc(1, sizeof(fairplay_t));
}
int fairplay_setup(fairplay_t *fp, const unsigned char req[16], unsigned char res[142]) {
    (void)fp; (void)req; memset(res, 0, 142); return 0;
}
int fairplay_handshake(fairplay_t *fp, const unsigned char req[164], unsigned char res[32]) {
    (void)fp; (void)req; memset(res, 0, 32); return 0;
}
int fairplay_decrypt(fairplay_t *fp, const unsigned char input[72], unsigned char output[16]) {
    (void)fp; (void)input; memset(output, 0, 16); return 0;   /* always succeeds */
}
void fairplay_destroy(fairplay_t *fp) { free(fp); }

/* ---------- airplay_video ---------- */
airplay_video_t *airplay_video_init(raop_t *raop, unsigned short port,
                                     const char *lang, const char *lang_sub,
                                     const char *lang_sys) {
    (void)raop; (void)port; (void)lang; (void)lang_sub; (void)lang_sys;
    return NULL;
}
void airplay_video_destroy(airplay_video_t *v) { (void)v; }
int  airplay_video_get_id(airplay_video_t *v)  { (void)v; return -1; }

/* mirror_buffer_init/destroy not called from raop.c; no stub needed here */

/* ---------- httpd extra (init/start/stop/destroy already above) ---------- */
bool httpd_nohold(httpd_t *h) { (void)h; return false; }
void httpd_remove_known_connections(httpd_t *h) { (void)h; }
void httpd_remove_connections_by_type(httpd_t *h, connection_type_t t) { (void)h; (void)t; }
int  httpd_set_connection_type(httpd_t *h, void *ud, connection_type_t t) { (void)h; (void)ud; (void)t; return 0; }
int  httpd_count_connection_type(httpd_t *h, connection_type_t t) { (void)h; (void)t; return 0; }
int  httpd_get_connection_socket(httpd_t *h, void *ud) { (void)h; (void)ud; return -1; }
int  httpd_get_connection_socket_by_type(httpd_t *h, connection_type_t t, int i) { (void)h; (void)t; (void)i; return -1; }
const char *httpd_get_connection_typename(connection_type_t t) { (void)t; return "stub"; }
int  httpd_is_running(httpd_t *h) { (void)h; return 0; }

/* ---------- raop_rtp extra ---------- */
void raop_rtp_start_audio(raop_rtp_t *r, unsigned short *crport, unsigned short *clport,
                           unsigned short *drport, unsigned char *ct, unsigned int *sr) {
    (void)r; (void)crport; (void)clport; (void)drport; (void)ct; (void)sr;
}
void raop_rtp_set_volume(raop_rtp_t *r, float v)                              { (void)r; (void)v; }
void raop_rtp_set_metadata(raop_rtp_t *r, const char *d, int l)               { (void)r; (void)d; (void)l; }
void raop_rtp_set_coverart(raop_rtp_t *r, const char *d, int l)               { (void)r; (void)d; (void)l; }
void raop_rtp_set_progress(raop_rtp_t *r, uint32_t s, uint32_t c, uint32_t e){ (void)r; (void)s; (void)c; (void)e; }
void raop_rtp_flush(raop_rtp_t *r, int n)                                      { (void)r; (void)n; }
int  raop_rtp_is_running(raop_rtp_t *r)                                        { (void)r; return 0; }

/* ---------- airplay_video / HLS playlist stubs ---------- */
#include "airplay_video.h"
void set_apple_session_id(airplay_video_t *v, const char *s, size_t l)         { (void)v; (void)s; (void)l; }
void set_start_position_seconds(airplay_video_t *v, float f)                   { (void)v; (void)f; }
void set_resume_position_seconds(airplay_video_t *v, float f)                  { (void)v; (void)f; }
float get_duration(airplay_video_t *v)                                          { (void)v; return 0.0f; }
float get_start_position_seconds(airplay_video_t *v)                           { (void)v; return 0.0f; }
float get_resume_position_seconds(airplay_video_t *v)                          { (void)v; return 0.0f; }
void set_playback_uuid(airplay_video_t *v, const char *s, size_t l)            { (void)v; (void)s; (void)l; }
void set_uri_prefix(airplay_video_t *v, const char *s, size_t l)               { (void)v; (void)s; (void)l; }
char *get_uri_local_prefix(airplay_video_t *v)                                 { (void)v; return NULL; }
void set_playback_location(airplay_video_t *v, const char *s, size_t l)        { (void)v; (void)s; (void)l; }
const char *get_playback_location(airplay_video_t *v)                          { (void)v; return NULL; }
const char *get_playback_uuid(airplay_video_t *v)                              { (void)v; return NULL; }
int  get_next_FCUP_RequestID(airplay_video_t *v)                               { (void)v; return 0; }
void set_next_media_uri_id(airplay_video_t *v, int i)                          { (void)v; (void)i; }
int  get_next_media_uri_id(airplay_video_t *v)                                 { (void)v; return 0; }
int  get_num_media_uri(airplay_video_t *v)                                     { (void)v; return 0; }
char *get_media_uri_by_num(airplay_video_t *v, int n)                          { (void)v; (void)n; return NULL; }
int  analyze_media_playlist(char *pl, float *dur, bool *end)                   { (void)pl; (void)dur; (void)end; return 0; }
void store_master_playlist(airplay_video_t *v, char *pl)                       { (void)v; (void)pl; }
int  store_media_playlist(airplay_video_t *v, char *pl, int *c, float *d, bool *e, int n) {
    (void)v; (void)pl; (void)c; (void)d; (void)e; (void)n; return 0;
}
char *get_master_playlist(airplay_video_t *v)                                  { (void)v; return NULL; }
char *get_media_playlist(airplay_video_t *v, int *c, float *d, const char *u) { (void)v; (void)c; (void)d; (void)u; return NULL; }
void create_media_data_store(airplay_video_t *v, char **s, int n)              { (void)v; (void)s; (void)n; }
int  create_media_uri_table(const char *p, const char *m, int l, char ***t, int *n) {
    (void)p; (void)m; (void)l; (void)t; (void)n; return -1;
}
char *adjust_master_playlist(char *d, int l, const char *p, char *lp)          { (void)d; (void)l; (void)p; (void)lp; return NULL; }
char *adjust_yt_condensed_playlist(const char *m, int c)                       { (void)m; (void)c; return NULL; }
char *select_master_playlist_language(airplay_video_t *v, char *m)             { (void)v; (void)m; return NULL; }
const char *get_uri_prefix(airplay_video_t *v)                                 { (void)v; return NULL; }
const char *get_apple_session_id(airplay_video_t *v)                           { (void)v; return NULL; }

/* ---------- mdnsd (sockets stubbed; txt_add is real) ---------- */
int mdnsd_txt_add(mdnsd_txt_t *txt, const char *key, const char *value) {
    if (!key || !value || !txt) return -1;
    int klen = (int)strlen(key), vlen = (int)strlen(value);
    int elen = klen + 1 + vlen;    /* "key=value" */
    if (elen > 255 || txt->length + 1 + elen > MDNSD_TXT_MAX) return -1;
    txt->bytes[txt->length] = (unsigned char)elen;
    memcpy(txt->bytes + txt->length + 1, key, klen);
    txt->bytes[txt->length + 1 + klen] = '=';
    memcpy(txt->bytes + txt->length + 2 + klen, value, vlen);
    txt->length += 1 + elen;
    return 0;
}
mdnsd_t *mdnsd_init(const char *host) { (void)host; return calloc(1, sizeof(mdnsd_t)); }
void mdnsd_destroy(mdnsd_t *m) { free(m); }
int  mdnsd_start(mdnsd_t *m)   { (void)m; return 0; }
void mdnsd_stop(mdnsd_t *m)    { (void)m; }
void mdnsd_announce(mdnsd_t *m, uint32_t ttl) { (void)m; (void)ttl; }
void mdnsd_goodbye(mdnsd_t *m, const mdnsd_service_t *s) { (void)m; (void)s; }
void mdnsd_set_services(mdnsd_t *m, const mdnsd_service_t *a, const mdnsd_service_t *r) {
    (void)m; (void)a; (void)r;
}

/* =========================================================
 * 3.  TEST INFRASTRUCTURE
 * ========================================================= */
static int g_failures = 0;
static int g_pass     = 0;

#define PASS(name)           do { printf("PASS  %s\n", (name)); g_pass++; } while(0)
#define FAIL(name, fmt, ...) do { \
    fprintf(stderr, "FAIL  %s: " fmt "\n", (name), ##__VA_ARGS__); \
    g_failures++; \
} while(0)
#define EXPECT_INT(name, got, want) do { \
    if ((int)(got) == (int)(want)) PASS(name); \
    else FAIL(name, "expected %d got %d", (int)(want), (int)(got)); \
} while(0)
#define EXPECT_STR(name, got, want) do { \
    if ((got) && strcmp((got),(want))==0) PASS(name); \
    else FAIL(name, "expected \"%s\" got \"%s\"", (want), (got)?(got):"(null)"); \
} while(0)
#define EXPECT_TRUE(name, cond)  do { if (cond) PASS(name); else FAIL(name, "condition false"); } while(0)
#define EXPECT_NULL(name, ptr)   do { if (!(ptr)) PASS(name); else FAIL(name, "expected NULL got %p", (void*)(ptr)); } while(0)
#define EXPECT_NONNULL(name, ptr) do { if (ptr) PASS(name); else FAIL(name, "expected non-NULL"); } while(0)

/* ---- Response inspection (parses serialised response->data string) ---- */
static int resp_code(http_response_t *r) {
    /* data = "RTSP/1.0 501 Not Implemented\r\n..." */
    if (!r || r->data_length < 9) return 0;
    const char *sp = memchr(r->data, ' ', (size_t)r->data_length);
    if (!sp) return 0;
    return atoi(sp + 1);
}

static char g_hdr_buf[4096];
static const char *resp_header(http_response_t *r, const char *name) {
    if (!r || !name) return NULL;
    size_t nlen = strlen(name);
    const char *p = r->data, *end = r->data + r->data_length;
    /* skip first status line */
    const char *eol = (const char *)memmem(p, (size_t)(end - p), "\r\n", 2);
    if (!eol) return NULL;
    p = eol + 2;
    while (p < end) {
        const char *next = (const char *)memmem(p, (size_t)(end - p), "\r\n", 2);
        if (!next) next = end;
        size_t linelen = (size_t)(next - p);
        if (linelen > nlen + 1 &&
            strncasecmp(p, name, nlen) == 0 && p[nlen] == ':') {
            const char *vs = p + nlen + 1;
            while (vs < next && (*vs == ' ' || *vs == '\t')) vs++;
            size_t vlen = (size_t)(next - vs);
            if (vlen >= sizeof(g_hdr_buf)) vlen = sizeof(g_hdr_buf) - 1;
            memcpy(g_hdr_buf, vs, vlen);
            g_hdr_buf[vlen] = '\0';
            return g_hdr_buf;
        }
        if (next == end) break;
        p = next + 2;
    }
    return NULL;
}

/* ---- TXT record field lookup (DNS TXT wire format) ----
 * Ring of buffers: callers may hold several returned pointers at once. */
static char g_txt_bufs[8][512];
static int  g_txt_idx = 0;
static char *txt_get(const unsigned char *bytes, int length, const char *key) {
    int klen = (int)strlen(key);
    const unsigned char *p = bytes, *end = bytes + length;
    while (p < end) {
        int elen = (int)*p++;
        if (p + elen > end) break;
        if (elen > klen + 1 &&
            memcmp(p, key, klen) == 0 && p[klen] == '=') {
            int vlen = elen - klen - 1;
            char *out = g_txt_bufs[g_txt_idx++ % 8];
            if (vlen >= 512) vlen = 511;
            memcpy(out, p + klen + 1, vlen);
            out[vlen] = '\0';
            return out;
        }
        p += elen;
    }
    return NULL;
}

/* ---- minimal raop_t and raop_conn_t factories ---- */
static void test_log_cb(void *cls, int level, const char *msg) {
    (void)cls; (void)level; (void)msg;
}
static double test_audio_set_client_volume(void *cls) { (void)cls; return 0.0; }

static raop_t *make_raop(void) {
    raop_t *raop = calloc(1, sizeof(raop_t));
    assert(raop);
    raop->logger = logger_init();
    logger_set_callback(raop->logger, test_log_cb, NULL);
    logger_set_level(raop->logger, LOGGER_ERR);
    /* /info unconditionally invokes this callback */
    raop->callbacks.audio_set_client_volume = test_audio_set_client_volume;
    int pres = 0;
    raop->pairing = pairing_init_generate("PocketAirDisplayTestDevice", "", &pres);
    raop->httpd = httpd_init(raop->logger, NULL, 0);
    /* rsakey: already a no-op stub */
    return raop;
}

static raop_conn_t *make_conn(raop_t *raop) {
    raop_conn_t *conn = calloc(1, sizeof(raop_conn_t));
    assert(conn);
    conn->raop    = raop;
    conn->fairplay = fairplay_init(raop->logger);
    conn->session  = pairing_session_init(raop->pairing);
    /* minimal 4-byte IPv4 loopback remote */
    static unsigned char lo[4] = {127, 0, 0, 1};
    conn->remote    = lo;
    conn->remotelen = 4;
    return conn;
}

static void free_conn(raop_conn_t *conn) {
    if (!conn) return;
    fairplay_destroy(conn->fairplay);
    if (conn->session) pairing_session_destroy(conn->session);
    if (conn->raop_ntp)        { raop_ntp_destroy(conn->raop_ntp);               conn->raop_ntp = NULL; }
    if (conn->raop_rtp)        { raop_rtp_destroy(conn->raop_rtp);               conn->raop_rtp = NULL; }
    if (conn->raop_rtp_mirror) { raop_rtp_mirror_destroy(conn->raop_rtp_mirror); conn->raop_rtp_mirror = NULL; }
    free(conn);
}

/* Build HTTP request from raw RTSP string (null-terminated) */
static http_request_t *make_request(const char *raw) {
    http_request_t *req = http_request_init();
    http_request_add_data(req, raw, (int)strlen(raw));
    return req;
}

/* Build HTTP request with binary body (Content-Length header added) */
static http_request_t *make_request_with_body(const char *header_raw,
                                               const char *body, int bodylen) {
    char hdr[1024];
    snprintf(hdr, sizeof(hdr), "%sContent-Length: %d\r\n\r\n", header_raw, bodylen);
    int hlen = (int)strlen(hdr);
    char *buf = malloc((size_t)(hlen + bodylen));
    assert(buf);
    memcpy(buf, hdr, hlen);
    memcpy(buf + hlen, body, bodylen);
    http_request_t *req = http_request_init();
    http_request_add_data(req, buf, hlen + bodylen);
    free(buf);
    return req;
}

/* dnssd instance for TXT / /info tests */
static dnssd_t *make_dnssd(void) {
    unsigned char hw[6] = {0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF};
    int err = 0;
    dnssd_t *d = dnssd_init("TestReceiver", 12, (const char *)hw, 6, 0, &err);
    assert(d && err == 0);
    static char pk_dummy[129];
    memset(pk_dummy, '0', 128);
    pk_dummy[128] = '\0';
    dnssd_set_pk(d, pk_dummy);
    return d;
}

/* =========================================================
 * 4.  TEST CASES
 * ========================================================= */

/* ---- 4.1  ANNOUNCE: unconditional 501, no state change ---- */
static void test_announce_valid_sdp_501(void) {
    raop_t *raop = make_raop();
    raop_conn_t *conn = make_conn(raop);
    http_response_t *resp = http_response_create();
    http_response_init(resp, "RTSP/1.0", 200, "OK");

    const char *sdp =
        "v=0\r\nm=audio 0 RTP/AVP 96\r\na=rtpmap:96 AppleLossless/44100/2\r\n";
    http_request_t *req = make_request_with_body(
        "ANNOUNCE rtsp://10.0.0.1/session RTSP/1.0\r\n"
        "Content-Type: application/sdp\r\n", sdp, (int)strlen(sdp));

    char *rd = NULL; int rl = 0;
    raop_handler_announce(conn, req, resp, &rd, &rl);

    EXPECT_INT("ANNOUNCE+SDP → 501", resp_code(resp), 501);
    EXPECT_TRUE("ANNOUNCE: legacy_audio not set",  !conn->legacy_audio);
    EXPECT_NULL("ANNOUNCE: raop_ntp not started",  conn->raop_ntp);

    http_request_destroy(req); http_response_destroy(resp);
    free_conn(conn); raop_destroy(raop);
}

static void test_announce_empty_body_501(void) {
    raop_t *raop = make_raop();
    raop_conn_t *conn = make_conn(raop);
    http_response_t *resp = http_response_create();
    http_response_init(resp, "RTSP/1.0", 200, "OK");

    http_request_t *req = make_request(
        "ANNOUNCE rtsp://10.0.0.1/s RTSP/1.0\r\n\r\n");

    char *rd = NULL; int rl = 0;
    raop_handler_announce(conn, req, resp, &rd, &rl);
    EXPECT_INT("ANNOUNCE empty → 501", resp_code(resp), 501);

    http_request_destroy(req); http_response_destroy(resp);
    free_conn(conn); raop_destroy(raop);
}

/* ---- 4.2  OPTIONS: Public header must not contain ANNOUNCE ---- */
static void test_options_no_announce(void) {
    raop_t *raop = make_raop();
    raop_conn_t *conn = make_conn(raop);
    http_response_t *resp = http_response_create();
    http_response_init(resp, "RTSP/1.0", 200, "OK");

    http_request_t *req = make_request("OPTIONS * RTSP/1.0\r\n\r\n");
    char *rd = NULL; int rl = 0;
    raop_handler_options(conn, req, resp, &rd, &rl);

    const char *pub = resp_header(resp, "Public");
    EXPECT_NONNULL("OPTIONS: Public header present", pub);
    if (pub) {
        EXPECT_TRUE("OPTIONS: ANNOUNCE absent from Public",
                    strstr(pub, "ANNOUNCE") == NULL);
        EXPECT_TRUE("OPTIONS: SETUP in Public",    strstr(pub, "SETUP")    != NULL);
        EXPECT_TRUE("OPTIONS: RECORD in Public",   strstr(pub, "RECORD")   != NULL);
        EXPECT_TRUE("OPTIONS: TEARDOWN in Public", strstr(pub, "TEARDOWN") != NULL);
        EXPECT_TRUE("OPTIONS: GET_PARAMETER in Public",
                    strstr(pub, "GET_PARAMETER") != NULL);
    }

    http_request_destroy(req); http_response_destroy(resp);
    free_conn(conn); raop_destroy(raop);
}

/* ---- 4.3  SETUP: malformed eiv (8 bytes instead of 16) → 456 ---- */
static void test_setup_eiv_short_456(void) {
    raop_t *raop = make_raop();
    raop_conn_t *conn = make_conn(raop);
    http_response_t *resp = http_response_create();
    http_response_init(resp, "RTSP/1.0", 200, "OK");

    plist_t p = plist_new_dict();
    char eiv[8] = {0}, ekey[72] = {0};
    plist_dict_set_item(p, "eiv",  plist_new_data(eiv,  8));   /* wrong: must be 16 */
    plist_dict_set_item(p, "ekey", plist_new_data(ekey, 72));
    char *bin = NULL; uint32_t blen = 0;
    plist_to_bin(p, &bin, &blen); plist_free(p);

    http_request_t *req = make_request_with_body(
        "SETUP rtsp://10.0.0.1/s RTSP/1.0\r\n", bin, (int)blen);
    free(bin);

    char *rd = NULL; int rl = 0;
    raop_handler_setup(conn, req, resp, &rd, &rl);
    EXPECT_INT("SETUP eiv=8bytes → 456", resp_code(resp), 456);

    http_request_destroy(req); http_response_destroy(resp);
    free_conn(conn); raop_destroy(raop);
}

/* ---- 4.4  SETUP: malformed ekey (8 bytes instead of 72) → 456 ---- */
static void test_setup_ekey_short_456(void) {
    raop_t *raop = make_raop();
    raop_conn_t *conn = make_conn(raop);
    http_response_t *resp = http_response_create();
    http_response_init(resp, "RTSP/1.0", 200, "OK");

    plist_t p = plist_new_dict();
    char eiv[16] = {0}, ekey[8] = {0};
    plist_dict_set_item(p, "eiv",  plist_new_data(eiv,  16));
    plist_dict_set_item(p, "ekey", plist_new_data(ekey,  8));  /* wrong: must be 72 */
    char *bin = NULL; uint32_t blen = 0;
    plist_to_bin(p, &bin, &blen); plist_free(p);

    http_request_t *req = make_request_with_body(
        "SETUP rtsp://10.0.0.1/s RTSP/1.0\r\n", bin, (int)blen);
    free(bin);

    char *rd = NULL; int rl = 0;
    raop_handler_setup(conn, req, resp, &rd, &rl);
    EXPECT_INT("SETUP ekey=8bytes → 456", resp_code(resp), 456);

    http_request_destroy(req); http_response_destroy(resp);
    free_conn(conn); raop_destroy(raop);
}

/* ---- 4.5  SETUP: NULL / non-plist body → 400, no crash ---- */
static void test_setup_null_body_safe(void) {
    raop_t *raop = make_raop();
    raop_conn_t *conn = make_conn(raop);
    http_response_t *resp = http_response_create();
    http_response_init(resp, "RTSP/1.0", 200, "OK");

    /* Empty body — plist_from_bin should return NULL gracefully */
    http_request_t *req = make_request(
        "SETUP rtsp://10.0.0.1/s RTSP/1.0\r\n\r\n");

    char *rd = NULL; int rl = 0;
    raop_handler_setup(conn, req, resp, &rd, &rl);
    /* No crash, and a missing body must be rejected instead of succeeding. */
    EXPECT_INT("SETUP null-body → 400", resp_code(resp), 400);

    http_request_destroy(req); http_response_destroy(resp);
    free_conn(conn); raop_destroy(raop);
}

/* ---- 4.5b  SETUP: non-dict plist root → 400 ---- */
static void test_setup_non_dict_root_400(void) {
    raop_t *raop = make_raop();
    raop_conn_t *conn = make_conn(raop);
    http_response_t *resp = http_response_create();
    http_response_init(resp, "RTSP/1.0", 200, "OK");

    plist_t p = plist_new_uint(42);   /* valid plist, wrong root type */
    char *bin = NULL; uint32_t blen = 0;
    plist_to_bin(p, &bin, &blen); plist_free(p);

    http_request_t *req = make_request_with_body(
        "SETUP rtsp://10.0.0.1/s RTSP/1.0\r\n", bin, (int)blen);
    free(bin);

    char *rd = NULL; int rl = 0;
    raop_handler_setup(conn, req, resp, &rd, &rl);
    EXPECT_INT("SETUP uint root → 400", resp_code(resp), 400);
    EXPECT_NULL("SETUP uint root: no response body", rd);

    http_request_destroy(req); http_response_destroy(resp);
    free_conn(conn); raop_destroy(raop);
}

/* ---- 4.5c  SETUP: eiv wrong type (string) with data ekey → 456 ---- */
static void test_setup_eiv_wrong_type_456(void) {
    raop_t *raop = make_raop();
    raop_conn_t *conn = make_conn(raop);
    http_response_t *resp = http_response_create();
    http_response_init(resp, "RTSP/1.0", 200, "OK");

    plist_t p = plist_new_dict();
    char ekey[72] = {0};
    plist_dict_set_item(p, "eiv",  plist_new_string("not-a-data-node")); /* wrong type */
    plist_dict_set_item(p, "ekey", plist_new_data(ekey, 72));
    char *bin = NULL; uint32_t blen = 0;
    plist_to_bin(p, &bin, &blen); plist_free(p);

    http_request_t *req = make_request_with_body(
        "SETUP rtsp://10.0.0.1/s RTSP/1.0\r\n", bin, (int)blen);
    free(bin);

    char *rd = NULL; int rl = 0;
    raop_handler_setup(conn, req, resp, &rd, &rl);
    EXPECT_INT("SETUP eiv string type → 456", resp_code(resp), 456);

    http_request_destroy(req); http_response_destroy(resp);
    free_conn(conn); raop_destroy(raop);
}

/* ---- 4.5d  SETUP: 'streams' present but not an array → 400 ---- */
static void test_setup_streams_wrong_type_400(void) {
    raop_t *raop = make_raop();
    raop_conn_t *conn = make_conn(raop);
    http_response_t *resp = http_response_create();
    http_response_init(resp, "RTSP/1.0", 200, "OK");

    plist_t p = plist_new_dict();
    plist_dict_set_item(p, "streams", plist_new_string("nope"));   /* wrong type */
    char *bin = NULL; uint32_t blen = 0;
    plist_to_bin(p, &bin, &blen); plist_free(p);

    http_request_t *req = make_request_with_body(
        "SETUP rtsp://10.0.0.1/s RTSP/1.0\r\n", bin, (int)blen);
    free(bin);

    char *rd = NULL; int rl = 0;
    raop_handler_setup(conn, req, resp, &rd, &rl);
    EXPECT_INT("SETUP streams string type → 400", resp_code(resp), 400);

    http_request_destroy(req); http_response_destroy(resp);
    free_conn(conn); raop_destroy(raop);
}

/* ---- 4.5e  SETUP: dict root with nothing to set up → 400 ---- */
static void test_setup_empty_dict_400(void) {
    raop_t *raop = make_raop();
    raop_conn_t *conn = make_conn(raop);
    http_response_t *resp = http_response_create();
    http_response_init(resp, "RTSP/1.0", 200, "OK");

    plist_t p = plist_new_dict();   /* valid dict: no ekey/eiv, no streams */
    char *bin = NULL; uint32_t blen = 0;
    plist_to_bin(p, &bin, &blen); plist_free(p);

    http_request_t *req = make_request_with_body(
        "SETUP rtsp://10.0.0.1/s RTSP/1.0\r\n", bin, (int)blen);
    free(bin);

    char *rd = NULL; int rl = 0;
    raop_handler_setup(conn, req, resp, &rd, &rl);
    EXPECT_INT("SETUP empty dict → 400", resp_code(resp), 400);

    http_request_destroy(req); http_response_destroy(resp);
    free_conn(conn); raop_destroy(raop);
}

/* ---- 4.6  SETUP: duplicate initial SETUP (workers running) → 503 ---- */
static void test_setup_duplicate_503(void) {
    raop_t *raop = make_raop();
    raop_conn_t *conn = make_conn(raop);
    /* Pre-set a running NTP worker */
    conn->raop_ntp = calloc(1, sizeof(raop_ntp_t));

    http_response_t *resp = http_response_create();
    http_response_init(resp, "RTSP/1.0", 200, "OK");

    plist_t p = plist_new_dict();
    char eiv[16] = {0}, ekey[72] = {0};
    plist_dict_set_item(p, "eiv",  plist_new_data(eiv,  16));
    plist_dict_set_item(p, "ekey", plist_new_data(ekey, 72));
    char *bin = NULL; uint32_t blen = 0;
    plist_to_bin(p, &bin, &blen); plist_free(p);

    http_request_t *req = make_request_with_body(
        "SETUP rtsp://10.0.0.1/s RTSP/1.0\r\n", bin, (int)blen);
    free(bin);

    char *rd = NULL; int rl = 0;
    raop_handler_setup(conn, req, resp, &rd, &rl);
    EXPECT_INT("SETUP duplicate initial → 503", resp_code(resp), 503);

    http_request_destroy(req); http_response_destroy(resp);
    if (conn->raop_ntp) { free(conn->raop_ntp); conn->raop_ntp = NULL; }
    free_conn(conn); raop_destroy(raop);
}

/* ---- 4.7  SETUP: NTP init failure → 503, no worker pointer left ---- */
static void test_setup_ntp_init_fail_503(void) {
    raop_t *raop = make_raop();
    raop_conn_t *conn = make_conn(raop);
    g_ntp_init_fail = 1;

    http_response_t *resp = http_response_create();
    http_response_init(resp, "RTSP/1.0", 200, "OK");

    plist_t p = plist_new_dict();
    char eiv[16] = {0}, ekey[72] = {0};
    plist_dict_set_item(p, "eiv",  plist_new_data(eiv,  16));
    plist_dict_set_item(p, "ekey", plist_new_data(ekey, 72));
    plist_dict_set_item(p, "timingPort", plist_new_uint(6001));
    char *bin = NULL; uint32_t blen = 0;
    plist_to_bin(p, &bin, &blen); plist_free(p);

    http_request_t *req = make_request_with_body(
        "SETUP rtsp://10.0.0.1/s RTSP/1.0\r\n", bin, (int)blen);
    free(bin);

    char *rd = NULL; int rl = 0;
    raop_handler_setup(conn, req, resp, &rd, &rl);
    EXPECT_INT("SETUP NTP init fail → 503",       resp_code(resp), 503);
    EXPECT_NULL("SETUP NTP fail: raop_ntp is NULL", conn->raop_ntp);

    g_ntp_init_fail = 0;
    http_request_destroy(req); http_response_destroy(resp);
    free_conn(conn); raop_destroy(raop);
}

/* ---- 4.8  SETUP streams: non-dict entry → disconnect ---- */
static void test_setup_streams_non_dict(void) {
    raop_t *raop = make_raop();
    raop_conn_t *conn = make_conn(raop);
    http_response_set_disconnect(http_response_create(), 0); /* suppress unused warning */

    http_response_t *resp = http_response_create();
    http_response_init(resp, "RTSP/1.0", 200, "OK");

    plist_t p = plist_new_dict();
    plist_t streams = plist_new_array();
    plist_array_append_item(streams, plist_new_string("bad"));   /* not a dict */
    plist_dict_set_item(p, "streams", streams);
    char *bin = NULL; uint32_t blen = 0;
    plist_to_bin(p, &bin, &blen); plist_free(p);

    http_request_t *req = make_request_with_body(
        "SETUP rtsp://10.0.0.1/s RTSP/1.0\r\n", bin, (int)blen);
    free(bin);

    char *rd = NULL; int rl = 0;
    raop_handler_setup(conn, req, resp, &rd, &rl);
    EXPECT_TRUE("SETUP streams non-dict → disconnect",
                http_response_get_disconnect(resp) != 0);

    http_request_destroy(req); http_response_destroy(resp);
    free_conn(conn); raop_destroy(raop);
}

/* ---- 4.9  SETUP type-110: zero streamConnectionID → disconnect ---- */
static void test_setup_type110_zero_cid(void) {
    raop_t *raop = make_raop();
    raop_conn_t *conn = make_conn(raop);
    /* Pre-init workers so we reach stream processing (skip initial SETUP block) */
    conn->raop_ntp        = calloc(1, sizeof(raop_ntp_t));
    conn->raop_rtp        = calloc(1, sizeof(raop_rtp_t));
    conn->raop_rtp_mirror = calloc(1, sizeof(raop_rtp_mirror_t));

    http_response_t *resp = http_response_create();
    http_response_init(resp, "RTSP/1.0", 200, "OK");

    plist_t p = plist_new_dict();
    plist_t streams = plist_new_array();
    plist_t stream = plist_new_dict();
    plist_dict_set_item(stream, "type", plist_new_uint(110));
    plist_dict_set_item(stream, "streamConnectionID", plist_new_uint(0)); /* zero = bad */
    plist_array_append_item(streams, stream);
    plist_dict_set_item(p, "streams", streams);
    char *bin = NULL; uint32_t blen = 0;
    plist_to_bin(p, &bin, &blen); plist_free(p);

    http_request_t *req = make_request_with_body(
        "SETUP rtsp://10.0.0.1/s RTSP/1.0\r\n", bin, (int)blen);
    free(bin);

    char *rd = NULL; int rl = 0;
    raop_handler_setup(conn, req, resp, &rd, &rl);
    EXPECT_TRUE("SETUP type-110 zero CID → disconnect",
                http_response_get_disconnect(resp) != 0);

    http_request_destroy(req); http_response_destroy(resp);
    if (conn->raop_ntp)        { free(conn->raop_ntp);        conn->raop_ntp = NULL; }
    if (conn->raop_rtp)        { free(conn->raop_rtp);        conn->raop_rtp = NULL; }
    if (conn->raop_rtp_mirror) { free(conn->raop_rtp_mirror); conn->raop_rtp_mirror = NULL; }
    free_conn(conn); raop_destroy(raop);
}

/* ---- 4.10  SETUP type-110: missing streamConnectionID → disconnect ---- */
static void test_setup_type110_missing_cid(void) {
    raop_t *raop = make_raop();
    raop_conn_t *conn = make_conn(raop);
    conn->raop_ntp        = calloc(1, sizeof(raop_ntp_t));
    conn->raop_rtp        = calloc(1, sizeof(raop_rtp_t));
    conn->raop_rtp_mirror = calloc(1, sizeof(raop_rtp_mirror_t));

    http_response_t *resp = http_response_create();
    http_response_init(resp, "RTSP/1.0", 200, "OK");

    plist_t p = plist_new_dict();
    plist_t streams = plist_new_array();
    plist_t stream = plist_new_dict();
    plist_dict_set_item(stream, "type", plist_new_uint(110));
    /* omit streamConnectionID */
    plist_array_append_item(streams, stream);
    plist_dict_set_item(p, "streams", streams);
    char *bin = NULL; uint32_t blen = 0;
    plist_to_bin(p, &bin, &blen); plist_free(p);

    http_request_t *req = make_request_with_body(
        "SETUP rtsp://10.0.0.1/s RTSP/1.0\r\n", bin, (int)blen);
    free(bin);

    char *rd = NULL; int rl = 0;
    raop_handler_setup(conn, req, resp, &rd, &rl);
    EXPECT_TRUE("SETUP type-110 missing CID → disconnect",
                http_response_get_disconnect(resp) != 0);

    http_request_destroy(req); http_response_destroy(resp);
    if (conn->raop_ntp)        { free(conn->raop_ntp);        conn->raop_ntp = NULL; }
    if (conn->raop_rtp)        { free(conn->raop_rtp);        conn->raop_rtp = NULL; }
    if (conn->raop_rtp_mirror) { free(conn->raop_rtp_mirror); conn->raop_rtp_mirror = NULL; }
    free_conn(conn); raop_destroy(raop);
}

/* ---- 4.10b  SETUP unknown stream type → disconnect ---- */
static void test_setup_stream_unknown_type(void) {
    raop_t *raop = make_raop();
    raop_conn_t *conn = make_conn(raop);

    http_response_t *resp = http_response_create();
    http_response_init(resp, "RTSP/1.0", 200, "OK");

    plist_t p = plist_new_dict();
    plist_t streams = plist_new_array();
    plist_t stream = plist_new_dict();
    plist_dict_set_item(stream, "type", plist_new_uint(999));  /* no such stream type */
    plist_array_append_item(streams, stream);
    plist_dict_set_item(p, "streams", streams);
    char *bin = NULL; uint32_t blen = 0;
    plist_to_bin(p, &bin, &blen); plist_free(p);

    http_request_t *req = make_request_with_body(
        "SETUP rtsp://10.0.0.1/s RTSP/1.0\r\n", bin, (int)blen);
    free(bin);

    char *rd = NULL; int rl = 0;
    raop_handler_setup(conn, req, resp, &rd, &rl);
    EXPECT_TRUE("SETUP unknown stream type → disconnect",
                http_response_get_disconnect(resp) != 0);

    http_request_destroy(req); http_response_destroy(resp);
    free_conn(conn); raop_destroy(raop);
}

/* ---- 4.10c  SETUP stream (type 110) before any initial key SETUP → disconnect ---- */
static void test_setup_stream_before_initial(void) {
    raop_t *raop = make_raop();
    raop_conn_t *conn = make_conn(raop);   /* no raop_ntp/rtp/mirror workers yet */

    http_response_t *resp = http_response_create();
    http_response_init(resp, "RTSP/1.0", 200, "OK");

    plist_t p = plist_new_dict();
    plist_t streams = plist_new_array();
    plist_t stream = plist_new_dict();
    plist_dict_set_item(stream, "type", plist_new_uint(110));
    plist_dict_set_item(stream, "streamConnectionID", plist_new_uint(0x1234));
    plist_array_append_item(streams, stream);
    plist_dict_set_item(p, "streams", streams);
    char *bin = NULL; uint32_t blen = 0;
    plist_to_bin(p, &bin, &blen); plist_free(p);

    http_request_t *req = make_request_with_body(
        "SETUP rtsp://10.0.0.1/s RTSP/1.0\r\n", bin, (int)blen);
    free(bin);

    char *rd = NULL; int rl = 0;
    raop_handler_setup(conn, req, resp, &rd, &rl);
    EXPECT_TRUE("SETUP stream before initial SETUP → disconnect",
                http_response_get_disconnect(resp) != 0);

    http_request_destroy(req); http_response_destroy(resp);
    free_conn(conn); raop_destroy(raop);
}

static void test_info_status_flags(void) {
    raop_t *raop = make_raop();
    raop_conn_t *conn = make_conn(raop);
    raop->dnssd = make_dnssd();
    memset(raop->pk_str, '0', 64);   /* 64 hex chars = 32 bytes = ED25519_KEY_SIZE */
    raop->pk_str[64] = '\0';

    http_response_t *resp = http_response_create();
    http_response_init(resp, "RTSP/1.0", 200, "OK");

    http_request_t *req = make_request(
        "GET /info RTSP/1.0\r\nCSeq: 1\r\n\r\n");

    char *rd = NULL; int rl = 0;
    raop_handler_info(conn, req, resp, &rd, &rl);

    EXPECT_INT("/info: returns 200", resp_code(resp), 200);

    if (rd && rl > 0) {
        plist_t pr = NULL;
        plist_from_bin(rd, rl, &pr);
        if (pr) {
            plist_t sf_node = plist_dict_get_item(pr, "statusFlags");
            if (sf_node && PLIST_IS_UINT(sf_node)) {
                uint64_t sf = 0;
                plist_get_uint_val(sf_node, &sf);
                EXPECT_INT("/info: statusFlags == 68",       (int)sf, 68);
                unsigned long macro_val = strtoul(AIRPLAY_FLAGS, NULL, 16);
                EXPECT_INT("/info: statusFlags matches AIRPLAY_FLAGS (0x44)",
                           (int)sf, (int)macro_val);
            } else {
                FAIL("/info statusFlags", "node missing or wrong type");
            }
            plist_free(pr);
        } else {
            FAIL("/info body", "plist_from_bin failed");
        }
        free(rd);
    } else {
        FAIL("/info body", "no response data");
    }

    http_request_destroy(req); http_response_destroy(resp);
    dnssd_destroy(raop->dnssd); raop->dnssd = NULL;
    free_conn(conn); raop_destroy(raop);
}

/* ---- 4.12  RAOP TXT: et=0, cn=0, ek=0, am != AirPort ---- */
static void test_raop_txt_fields(void) {
    dnssd_t *d = make_dnssd();
    int ret = dnssd_register_raop(d, 7000);
    EXPECT_INT("dnssd_register_raop succeeds", ret, 0);

    int len = 0;
    const char *raw = dnssd_get_raop_txt(d, &len);
    EXPECT_TRUE("RAOP TXT non-empty", raw != NULL && len > 0);

    if (raw && len > 0) {
        const char *et = txt_get((const unsigned char *)raw, len, "et");
        const char *cn = txt_get((const unsigned char *)raw, len, "cn");
        const char *ek = txt_get((const unsigned char *)raw, len, "ek");
        const char *am = txt_get((const unsigned char *)raw, len, "am");

        EXPECT_STR("RAOP TXT et=0 (no RSA encryption)",      et, "0");
        EXPECT_STR("RAOP TXT cn=0 (ALAC not supported)",     cn, "0");
        EXPECT_STR("RAOP TXT ek=0 (no RSA key)",             ek, "0");
        EXPECT_TRUE("RAOP TXT am field present",              am != NULL);
        if (am) {
            EXPECT_TRUE("RAOP TXT am not AirPort model",
                        strncmp(am, "AirPort", 7) != 0);
            printf("      RAOP TXT am=%s\n", am);
        }
    }

    dnssd_destroy(d);
}

/* ---- 4.13  AirPlay TXT flags must equal /info statusFlags (0x44) ----
 *
 * KNOWN DEFECT: dnssd_mdnsd.c dnssd_build_airplay_txt() hardcodes "0x4"
 * instead of using AIRPLAY_FLAGS ("0x44").  This test will FAIL until fixed.
 */
static void test_airplay_txt_flags_consistency(void) {
    dnssd_t *d = make_dnssd();
    int ret = dnssd_register_airplay(d, 7000);
    EXPECT_INT("dnssd_register_airplay succeeds", ret, 0);

    int len = 0;
    const char *raw = dnssd_get_airplay_txt(d, &len);
    EXPECT_TRUE("AirPlay TXT non-empty", raw != NULL && len > 0);

    if (raw && len > 0) {
        const char *flags = txt_get((const unsigned char *)raw, len, "flags");
        EXPECT_TRUE("AirPlay TXT: flags field present", flags != NULL);

        if (flags) {
            unsigned long txt_flags  = strtoul(flags, NULL, 16);
            unsigned long info_flags = strtoul(AIRPLAY_FLAGS, NULL, 16); /* 0x44 = 68 */

            printf("      AirPlay TXT flags=%-6s (0x%02lx)   AIRPLAY_FLAGS=0x%02lx\n",
                   flags, txt_flags, info_flags);

            /* This will FAIL if dnssd_mdnsd.c has "0x4" instead of AIRPLAY_FLAGS */
            EXPECT_INT("AirPlay TXT flags == AIRPLAY_FLAGS (0x44)",
                       (int)txt_flags, (int)info_flags);
        }
    }

    dnssd_destroy(d);
}

/* =========================================================
 * 5.  MAIN
 * ========================================================= */
int main(void) {
    printf("=== Pocket AirDisplay core protocol test (production handlers) ===\n\n");

    printf("-- ANNOUNCE --\n");
    test_announce_valid_sdp_501();
    test_announce_empty_body_501();

    printf("\n-- OPTIONS --\n");
    test_options_no_announce();

    printf("\n-- SETUP malformed inputs --\n");
    test_setup_eiv_short_456();
    test_setup_ekey_short_456();
    test_setup_null_body_safe();
    test_setup_non_dict_root_400();
    test_setup_eiv_wrong_type_456();
    test_setup_streams_wrong_type_400();
    test_setup_empty_dict_400();
    test_setup_duplicate_503();
    test_setup_ntp_init_fail_503();

    printf("\n-- SETUP stream validation --\n");
    test_setup_streams_non_dict();
    test_setup_type110_zero_cid();
    test_setup_type110_missing_cid();
    test_setup_stream_unknown_type();
    test_setup_stream_before_initial();

    printf("\n-- /info metadata --\n");
    test_info_status_flags();

    printf("\n-- Discovery TXT records --\n");
    test_raop_txt_fields();
    test_airplay_txt_flags_consistency();

    printf("\n=== %d passed, %d failed ===\n", g_pass, g_failures);
    return g_failures ? 1 : 0;
}
