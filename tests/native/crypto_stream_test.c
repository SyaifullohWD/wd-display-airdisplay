#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <openssl/evp.h>
#include "mirror_buffer.h"

static void reference(uint64_t id, const unsigned char *audio, unsigned char *out, int len) {
    unsigned char key[64], iv[64], input[4096];
    char name[80]; unsigned int n; int written;
    EVP_MD_CTX *md = EVP_MD_CTX_new();
    snprintf(name, sizeof(name), "AirPlayStreamKey%llu", (unsigned long long)id);
    assert(EVP_DigestInit_ex(md, EVP_sha512(), NULL));
    assert(EVP_DigestUpdate(md, name, strlen(name)));
    assert(EVP_DigestUpdate(md, audio, 16)); assert(EVP_DigestFinal_ex(md, key, &n));
    snprintf(name, sizeof(name), "AirPlayStreamIV%llu", (unsigned long long)id);
    assert(EVP_DigestInit_ex(md, EVP_sha512(), NULL));
    assert(EVP_DigestUpdate(md, name, strlen(name)));
    assert(EVP_DigestUpdate(md, audio, 16)); assert(EVP_DigestFinal_ex(md, iv, &n));
    EVP_MD_CTX_free(md);
    for(int i=0;i<len;i++) input[i]=(unsigned char)(i*17+3);
    EVP_CIPHER_CTX *c = EVP_CIPHER_CTX_new();
    assert(EVP_EncryptInit_ex(c, EVP_aes_128_ctr(), NULL, key, iv));
    assert(EVP_EncryptUpdate(c, out, &written, input, len)); assert(written==len);
    EVP_CIPHER_CTX_free(c);
}
int main(void) {
    unsigned char audio[16]={1,2,3}; uint64_t id=123456789;
    unsigned char expected[4096]; reference(id,audio,expected,sizeof(expected));
    for(int first=1;first<=16;first++) {
        mirror_buffer_t *b=mirror_buffer_init(NULL,audio); mirror_buffer_init_aes(b,&id);
        int offset=0;
        for(int packet=0;packet<250;packet++) {
            int len=packet==0?first:(packet<32?1:1+(packet*13)%29);
            unsigned char *in=malloc(len), *out=malloc(len);
            for(int i=0;i<len;i++) in[i]=(unsigned char)((offset+i)*17+3);
            mirror_buffer_decrypt(b,in,out,len);
            assert(!memcmp(out,expected+offset,len)); offset+=len;
            free(in);free(out);
        }
        mirror_buffer_destroy(b);
    }
    puts("PASS: all 16 offsets, consecutive one-byte and mixed packets match continuous EVP AES-CTR");
}
