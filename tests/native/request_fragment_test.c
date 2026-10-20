#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include "http_request.h"
static void feed(http_request_t *r,const char *data,size_t len) {
    if (!len) return;
    char *exact=malloc(len); memcpy(exact,data,len);
    http_request_add_data(r,exact,(int)len); free(exact);
    assert(!http_request_has_error(r));
}
int main(void) {
    const char *protocols[]={"RTSP/1.0","HTTP/1.1","HTTP/1.0"};
    for(int p=0;p<3;p++) {
        char line[128]; snprintf(line,sizeof(line),"OPTIONS /some/long/url %s\r\nCSeq: 1\r\n\r\n",protocols[p]);
        size_t n=strlen(line);
        for(size_t split=1;split<n;split++) {
            http_request_t *r=http_request_init();
            feed(r,line,split);feed(r,line+split,n-split);
            assert(http_request_is_complete(r));
            assert(!strcmp(http_request_get_protocol(r),protocols[p]));
            assert(!strcmp(http_request_get_url(r),"/some/long/url"));
            http_request_destroy(r);
        }
        http_request_t *r=http_request_init();
        for(size_t i=0;i<n;i++) feed(r,line+i,1);
        assert(http_request_is_complete(r));assert(!strcmp(http_request_get_protocol(r),protocols[p]));
        http_request_destroy(r);
    }
    puts("PASS: exact allocations, every split and bytewise RTSP/HTTP protocol parsing");
}
