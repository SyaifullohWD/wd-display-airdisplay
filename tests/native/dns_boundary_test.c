/* Compile real DNS encoder and registration code together. Never call a network
 * start for valid services; an invalid-start test traps socket() before any IO. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
static int forbidden_socket(int domain,int type,int protocol){assert(!"invalid DNS must be rejected before socket()");return -1;}
#define socket forbidden_socket
#include "mdnsd/mdnsd.c"
#undef socket
#include "mdnsd/dnssd_mdnsd.c"
#include "dnssd.c"
static void check(const char *name,int accepted){
    const char hw[6]={1,2,3,4,5,6};int error=-99;
    dnssd_t *d=dnssd_init(name,(int)strlen(name),hw,6,0,&error);
    if(!accepted){assert(!d);assert(error==DNSSD_ERROR_BADNAME);return;}
    assert(d && error==0);
    dnssd_private_t *p=d->dnssd_private;mdnsd_service_t service;mdns_packet_t packet;
    dnssd_fill_raop_service(p,&service);service.registered=1;service.port=7000;
    assert(!mdns_build_response(p->mdnsd,&packet,&service,1,4500,MDNS_FAMILY_IPV4));
    /* Read real RR names and verify full RAOP label, not split/truncated text. */
    size_t pos=12;char decoded[256];assert(!mdns_read_name(packet.bytes,packet.length,&pos,decoded,sizeof(decoded)));
    assert(!strcmp(decoded,"_services._dns-sd._udp.local"));pos+=8;unsigned rdlen=mdns_read_u16(packet.bytes+pos);pos+=2+rdlen;
    assert(!mdns_read_name(packet.bytes,packet.length,&pos,decoded,sizeof(decoded)));
    assert(!strcmp(decoded,"_raop._tcp.local"));pos+=8;rdlen=mdns_read_u16(packet.bytes+pos);pos+=2;
    size_t end=pos+rdlen;assert(!mdns_read_name(packet.bytes,packet.length,&pos,decoded,sizeof(decoded)));assert(pos==end);
    assert(!strcmp(decoded,p->raop_name));assert(packet.bytes[end-rdlen]==strlen(name)+13);
    dnssd_fill_airplay_service(p,&service);service.registered=1;service.port=7000;
    assert(!mdns_build_response(p->mdnsd,&packet,&service,1,4500,MDNS_FAMILY_IPV6));
    dnssd_destroy(d);
}
int main(int argc,char **argv){
    if(argc>1){
        mdnsd_t *m=mdnsd_init("valid.local");mdnsd_service_t s={0};s.registered=1;s.port=7000;
        memset(s.name,'x',64);strcpy(s.name+64,"._raop._tcp.local");strcpy(s.type,"_raop._tcp.local");
        mdnsd_set_services(m,NULL,&s);assert(mdnsd_start(m)<0);mdnsd_destroy(m);
        puts("PASS: registration rejects unserializable DNS before sockets");return 0;
    }
    char ascii[80];memset(ascii,'x',50);ascii[50]=0;check(ascii,1);ascii[50]='x';ascii[51]=0;check(ascii,0);
    char utf8[80];for(int i=0;i<25;i++){utf8[i*2]=(char)0xc3;utf8[i*2+1]=(char)0xa9;}
    utf8[50]=0;check(utf8,1);utf8[50]='x';utf8[51]=0;check(utf8,0);
    const char emoji[]="\xf0\x9f\x98\x80";
    for(int i=0;i<12;i++)memcpy(utf8+4*i,emoji,4);
    utf8[48]='x';utf8[49]='x';utf8[50]=0;check(utf8,1);
    utf8[50]='x';utf8[51]=0;check(utf8,0);
    check("",0);memset(ascii,'z',63);ascii[63]=0;check(ascii,0);
    mdns_packet_t p={0};char label[66];memset(label,'x',63);label[63]=0;assert(!mdns_put_name(&p,label));assert(p.bytes[0]==63&&p.length==65);
    label[63]='x';label[64]=0;p.length=0;assert(mdns_put_name(&p,label)<0);
    puts("PASS: real DNS serialization, 63-byte labels, 13-byte RAOP prefix and UTF-8 50/51-byte receiver boundaries");
}
