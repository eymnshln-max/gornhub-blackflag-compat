// Read only: exact, build-specific caller stack layout from disassembly.
#include <dlfcn.h>
#include <mach/mach.h>
#include <mach/mach_vm.h>

static char sourceStateKey;static unsigned sourceSamples;
#include "source_state_decode.h"
__attribute__((noinline))static id sourceAttachments(id d,SEL s){void*ra=__builtin_return_address(0);Dl_info di;BOOL matched=NO;uintptr_t off=0;if(dladdr(ra,&di)&&di.dli_fname&&strstr(di.dli_fname,"D3DMetal.framework")){off=(uintptr_t)ra-(uintptr_t)di.dli_fbase;matched=off==0x112ec6||off==0x113265;}

#ifdef BF_SOURCE_STACK_CONTROL
 // Only compiled into the standalone control executable, never the game dylib.
 extern char sourceFixtureReturn;
 if(ra==(void*)&sourceFixtureReturn){matched=YES;off=0;}
#endif
 NSDictionary*state=nil;if(matched)state=sourceDecode((uintptr_t)__builtin_frame_address(0)+16);id a=((id(*)(id,SEL))previous(d,s))(d,s);if(state){objc_setAssociatedObject(a,&sourceStateKey,state,OBJC_ASSOCIATION_RETAIN_NONATOMIC);@synchronized(methods){if(sourceSamples++<10000){NSMutableDictionary*m=[state mutableCopy];m[@"callerOffset"]=@(off);event(@"original-source-state",m);[m release];}}}else if(matched)event(@"source-read-failed",@{@"callerOffset":@(off)});return a;}
static void sourceInstall(void){id a=[MTLRenderPipelineDescriptor new];hook(object_getClass(a),@selector(colorAttachments),(IMP)sourceAttachments);[a release];id b=[MTLMeshRenderPipelineDescriptor new];hook(object_getClass(b),@selector(colorAttachments),(IMP)sourceAttachments);[b release];}
