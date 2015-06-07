#define _GNU_SOURCE

#include <stdio.h>
#include <dlfcn.h>

static void* (*real_malloc)(size_t)=NULL;

static void mtrace_init(void)
{
    srand (time(NULL));

    real_malloc = dlsym(RTLD_NEXT, "malloc");
    if (NULL == real_malloc) {
        fprintf(stderr, "Error in `dlsym`: %s\n", dlerror());
    }
}

void *malloc(size_t size)
{
    if(real_malloc==NULL) {
        mtrace_init();
    }

    // hier mit 10% wahrscheinlichkeit NULL zurückgeben, ansonsten malloc() durchreichen
    short variable;
    variable=rand()%100;
    void *p = NULL;

    if(variable<=10) return p; // NULL (simuliert vollen speicher)
    
    // fprintf(stderr, "malloc(%d) = ", size);
    p = real_malloc(size);
    // fprintf(stderr, "%p\n", p);
    return p;
}
