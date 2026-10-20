/* Internal seam only supplies an AF_UNIX connection; production worker/parser,
 * select, recv, framing, cleanup and stop/join run unchanged. No listening socket. */
#include <assert.h>
#include <stdatomic.h>
#include <time.h>
#include <signal.h>
#if !defined(HTTPD_REQUEST_TIMEOUT_MS) && !defined(HTTPD_TEST_PRODUCTION_BUDGET)
#define HTTPD_REQUEST_TIMEOUT_MS 250
#endif
#include "httpd.c"
static atomic_int requests, destroyed;
static int large_response;
static void *init(void *o,unsigned char *l,int ll,unsigned char *r,int rl,unsigned int z){return &requests;}
static void destroy(void *p){atomic_fetch_add(&destroyed,1);}
static void request(void *p,http_request_t *r,http_response_t **out){
    assert(!strcmp(http_request_get_url(r),"/info"));
    assert(!strcmp(http_request_get_protocol(r),"RTSP/1.0"));
    *out=http_response_create();http_response_init(*out,"RTSP/1.0",200,"OK");
    if(large_response){char *body=calloc(1,4*1024*1024);assert(body);http_response_finish(*out,body,4*1024*1024);free(body);}
    else http_response_finish(*out,"ok",2);
    atomic_fetch_add(&requests,1);
}
static double now(void){struct timespec ts;clock_gettime(CLOCK_MONOTONIC,&ts);return ts.tv_sec+ts.tv_nsec/1e9;}
static httpd_t *start(logger_t *l,int pair[2]){
    httpd_callbacks_t cb={.conn_init=init,.conn_request=request,.conn_destroy=destroy};
    httpd_t *h=httpd_init(l,&cb,0);h->server_fd4=h->server_fd6=-1;
    assert(!socketpair(AF_UNIX,SOCK_STREAM,0,pair));
    assert(!httpd_add_connection(h,pair[0],NULL,0,NULL,0,0));
    h->running=1;h->joined=0;THREAD_CREATE(h->thread,httpd_thread,h);return h;
}
int main(int argc,char **argv){
    alarm(HTTPD_REQUEST_TIMEOUT_MS/1000+4); logger_t *l=logger_init();logger_set_level(l,LOGGER_ERR);
    large_response=argc>1 && !strcmp(argv[1],"backpressure");
    double began=now();int pair[2];httpd_t *h=start(l,pair);
    if(argc>1 && (!strcmp(argv[1],"valid")||large_response)){
        const char *line="GET /info RTSP/1.0\r\nCSeq: 1\r\n\r\n";
        for(size_t i=0;i<strlen(line);i++){assert(send(pair[1],line+i,1,0)==1);usleep(2000);}
        double end=now()+1;while(!atomic_load(&requests)&&now()<end)usleep(1000);
        assert(atomic_load(&requests)==1);
        if(large_response)usleep(50000); /* fill the unread peer's socket buffer */
        if(!large_response){char reply[256]={0};assert(recv(pair[1],reply,255,0)>0);assert(strstr(reply,"RTSP/1.0 200 OK"));}
    }else{
        int bytes=argc>1 && argv[1][0]>='0' && argv[1][0]<='7'?atoi(argv[1]):3;
        if(bytes)assert(send(pair[1],"GET /in",bytes,0)==bytes);usleep(50000);
        if(argc>1 && !strcmp(argv[1],"deadline")){
            double end=now()+HTTPD_REQUEST_TIMEOUT_MS/1000.0+0.75;while(!atomic_load(&destroyed)&&now()<end)usleep(1000);
            assert(atomic_load(&destroyed)==1);
            double deadline_elapsed=now()-began;
            printf("request_deadline_seconds=%.6f (budget_ms=%d)\n",deadline_elapsed,HTTPD_REQUEST_TIMEOUT_MS);
            assert(deadline_elapsed >= HTTPD_REQUEST_TIMEOUT_MS/1000.0-0.02);
        }
    }
    double t=now();httpd_stop(h);double elapsed=now()-t;
    printf("stop_seconds=%.6f\n",elapsed);assert(elapsed<0.20);
    assert(atomic_load(&destroyed)==1);assert(!httpd_is_running(h));
    httpd_destroy(h);close(pair[1]);logger_destroy(l);alarm(0);
    puts("PASS: isolated socketpair control framing/shutdown");
}
