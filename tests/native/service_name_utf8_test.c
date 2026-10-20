/* Same UTF-16 conversion used at the JNI boundary, no sockets/JVM stand-ins. */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "service_name_utf8.h"
int main(void) {
    uint16_t name[64]; char out[51];
    for (int i=0;i<12;i++) { name[2*i]=0xd83d; name[2*i+1]=0xde00; }
    name[24]='x'; name[25]='x';
    assert(service_name_utf8(name,26,out,sizeof(out))==50);
    for (int i=0;i<12;i++) assert(!memcmp(out+4*i,"\xf0\x9f\x98\x80",4));
    assert(!strcmp(out+48,"xx"));
    name[26]='x'; assert(service_name_utf8(name,27,out,sizeof(out))<0);
    for(int i=0;i<25;i++) name[i]=0xe9;
    assert(service_name_utf8(name,25,out,sizeof(out))==50);
    for(int i=0;i<50;i++) name[i]='a';
    assert(service_name_utf8(name,50,out,sizeof(out))==50);
    assert(out[50]==0);
    name[50]='a'; assert(service_name_utf8(name,51,out,sizeof(out))<0);
    name[0]=0; assert(service_name_utf8(name,1,out,sizeof(out))<0);
    name[0]=0xd83d; assert(service_name_utf8(name,1,out,sizeof(out))<0);
    name[0]=0xde00; assert(service_name_utf8(name,1,out,sizeof(out))<0);
    name[0]=0xd83d; name[1]='x'; assert(service_name_utf8(name,2,out,sizeof(out))<0);
    name[0]=0x20ac; assert(service_name_utf8(name,1,out,sizeof(out))==3);
    assert(!memcmp(out,"\xe2\x82\xac",4));
    assert(service_name_utf8(name,1,out,3)<0);
    assert(service_name_utf8(name,0,out,sizeof(out))<0);
    puts("PASS: JNI UTF-16 to standard UTF-8, 50/51-byte emoji/accent/ASCII boundaries, invalid surrogate/NUL rejection");
}
