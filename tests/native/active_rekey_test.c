/* Real mirror worker and crypto; only clock synchronization is isolated (no UDP).
 * TCP listener is explicitly bound to 127.0.0.1, never wildcard/mDNS. */
#include <stdatomic.h>
#include "raop_rtp_mirror.c"
uint64_t raop_ntp_timestamp_to_nano_seconds(uint64_t n,bool epoch){return n;}
uint64_t raop_ntp_get_local_time(void){return 0;}
uint64_t raop_ntp_convert_remote_time(raop_ntp_t *n,uint64_t t){return t;}
void raop_ntp_set_video_arrival_offset(raop_ntp_t *n,const uint64_t *o){}
static atomic_int videos, exited, allow_exit;
static void video(void *c,raop_ntp_t *n,video_decode_struct *v){
    const unsigned char expected[]={0,0,0,1,0x65,0x22};
    assert(v->data_len==6);assert(!memcmp(v->data,expected,6));atomic_fetch_add(&videos,1);
}
static void noop(void *c){}
static void reset(void *c,reset_type_t t){}
static void conn_reset(void *c,int r){}
static void running(void *c,bool b){if(!b){atomic_store(&exited,1);while(!atomic_load(&allow_exit))usleep(1000);}}
static void wait_video(int n){for(int i=0;i<1000&&atomic_load(&videos)<n;i++)usleep(1000);assert(atomic_load(&videos)==n);}
static void packet(int fd,mirror_buffer_t *sender){
    unsigned char header[128]={6}, plain[6]={0,0,0,2,0x65,0x22},cipher[6];
    mirror_buffer_decrypt(sender,plain,cipher,6);
    assert(send(fd,header,128,0)==128);assert(send(fd,cipher,6,0)==6);
}
int main(void){
    alarm(5);signal(SIGPIPE,SIG_IGN);
    logger_t *log=logger_init();logger_set_level(log,LOGGER_ERR);
    raop_callbacks_t cb={0};cb.video_process=video;cb.video_pause=noop;cb.video_reset=reset;
    cb.conn_reset=conn_reset;cb.mirror_video_running=running;
    unsigned char key[16]={1,2,3};uint64_t id=12345;
    raop_rtp_mirror_t *m=raop_rtp_mirror_init(log,&cb,(raop_ntp_t *)1,"127.0.0.1",4,key);
    assert(m);assert(!raop_rtp_mirror_init_aes(m,&id));
    mirror_buffer_t *sender=mirror_buffer_init(log,key);mirror_buffer_init_aes(sender,&id);
    int listener=socket(AF_INET,SOCK_STREAM,0);assert(listener>=0);
    struct sockaddr_in addr={.sin_family=AF_INET,.sin_addr.s_addr=htonl(INADDR_LOOPBACK)};
    assert(!bind(listener,(struct sockaddr *)&addr,sizeof(addr)));assert(!listen(listener,1));
    socklen_t len=sizeof(addr);assert(!getsockname(listener,(struct sockaddr *)&addr,&len));
    m->mirror_data_sock=listener;m->mirror_data_lport=ntohs(addr.sin_port);m->running=1;m->joined=0;
    THREAD_CREATE(m->thread_mirror,raop_rtp_mirror_thread,m);
    int fd=socket(AF_INET,SOCK_STREAM,0);assert(!connect(fd,(struct sockaddr *)&addr,sizeof(addr)));
    packet(fd,sender);wait_video(1);
    /* Duplicate type110 SETUP enters this production boundary before start's
     * already-running check. The second packet must retain its CTR offset. */
    assert(!raop_rtp_mirror_init_aes(m,&id));
    uint64_t other_id=id+1;assert(raop_rtp_mirror_init_aes(m,&other_id)==-1);
    unsigned short port=0;raop_rtp_mirror_start(m,&port,0);
    assert(port==ntohs(addr.sin_port));
    packet(fd,sender);wait_video(2);
    for(int i=0;i<80;i++){packet(fd,sender);assert(!raop_rtp_mirror_init_aes(m,&id));assert(raop_rtp_mirror_init_aes(m,&other_id)==-1);wait_video(i+3);}
    shutdown(fd,SHUT_WR);
    for(int i=0;i<1000&&!atomic_load(&exited);i++)usleep(1000);assert(atomic_load(&exited));
    assert(raop_rtp_mirror_init_aes(m,&other_id)==-1); /* running=false but not joined */
    atomic_store(&allow_exit,1);raop_rtp_mirror_stop(m);close(fd);
    assert(!raop_rtp_mirror_init_aes(m,&other_id)); /* valid new stream after join */
    mirror_buffer_init_aes(sender,&other_id);
    unsigned char plain[7]={1,2,3,4,5,6,7},cipher[7],decoded[7];
    mirror_buffer_decrypt(sender,plain,cipher,7);mirror_buffer_decrypt(m->buffer,cipher,decoded,7);
    assert(!memcmp(plain,decoded,7));
    raop_rtp_mirror_destroy(m);mirror_buffer_destroy(sender);logger_destroy(log);
    alarm(0);puts("PASS: active duplicate SETUP preserves real worker AES stream (82 packets)");
}
