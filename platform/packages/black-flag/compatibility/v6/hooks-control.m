#import <Foundation/Foundation.h>
#import <objc/runtime.h>
#include <pthread.h>
#include <assert.h>
#include <time.h>
static NSMutableDictionary *methods;
#include "hooks.h"
@interface BFParent:NSObject
-(int)value;
@end
@implementation BFParent
-(int)value{return 7;}
@end
@interface BFChild:BFParent
@end
@implementation BFChild
@end
static int own(id o,SEL s){return 11;}
static int wrapped(id o,SEL s){return ((int(*)(id,SEL))previous(o,s))(o,s)+1;}

static IMP slowPrevious(id obj,SEL s){@synchronized(methods){for(Class c=object_getClass(obj);c;c=class_getSuperclass(c)){NSValue*v=methods[[NSString stringWithFormat:@"%p:%s",c,sel_getName(s)]];if(v)return v.pointerValue;}}abort();}
static double now(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec*1e-9;}
int main(void){@autoreleasepool{
 methods=[NSMutableDictionary new];BFChild *obj=[BFChild new];SEL s=@selector(value);
 hook(BFParent.class,s,(IMP)wrapped);assert([obj value]==8);
 dispatch_semaphore_t ready=dispatch_semaphore_create(0),go=dispatch_semaphore_create(0),done=dispatch_semaphore_create(0);
 dispatch_async(dispatch_get_global_queue(0,0),^{@autoreleasepool{
  for(int i=0;i<1000;i++)assert([obj value]==8);
  dispatch_semaphore_signal(ready);dispatch_semaphore_wait(go,DISPATCH_TIME_FOREVER);
  for(int i=0;i<1000;i++)assert([obj value]==12);
  dispatch_semaphore_signal(done);
 }});
 assert(dispatch_semaphore_wait(ready,dispatch_time(DISPATCH_TIME_NOW,5*NSEC_PER_SEC))==0);
 assert(class_addMethod(BFChild.class,s,(IMP)own,method_getTypeEncoding(class_getInstanceMethod(BFParent.class,s))));
 hook(BFChild.class,s,(IMP)wrapped);assert([obj value]==12);
 dispatch_semaphore_signal(go);assert(dispatch_semaphore_wait(done,dispatch_time(DISPATCH_TIME_NOW,5*NSEC_PER_SEC))==0);
 for(int i=0;i<1000;i++){hook(BFChild.class,s,(IMP)wrapped);assert([obj value]==12);}
 int n=200000;IMP volatile sink;double a=now();
 for(int i=0;i<n;i++){@autoreleasepool{sink=slowPrevious(obj,s);}}
 double slow=now()-a;a=now();
 for(int i=0;i<n;i++){@autoreleasepool{sink=previous(obj,s);}}
 double fast=now()-a;(void)sink;
 printf("PASS inherited hook, same-thread and cross-thread invalidation, repeated installation. Lookup-only benchmark: old=%.6fs cached=%.6fs (%d calls). Not game FPS.\n",slow,fast,n);
 [obj release];return 0;
}}
