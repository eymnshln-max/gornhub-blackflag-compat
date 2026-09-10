#import <Foundation/Foundation.h>
#import <Metal/Metal.h>
#import <objc/runtime.h>
#include <crt_externs.h>
#include <unistd.h>
static NSMutableDictionary*methods;static BOOL testing=NO;static char writerPipelineKey,writerPassKey;
#include "hooks.h"
// Only repair errors and startup are logged, no frames, memory dumps or counters.
static void event(NSString*k,NSDictionary*d){if([k containsString:@"failed"])fprintf(stderr,"Black Flag compatibility: %s %s\n",k.UTF8String,[[d description] UTF8String]);}
#include "pipeline_info.h"
static NSDictionary*renderInfo(MTLRenderPipelineDescriptor*d){return fullPipelineInfo(d);}
#include "source_state.h"
#include "pipeline_info_chain.h"
#include "attachment_repair.h"
#include "scene_template_restore.h"
#include "source_restore_mesh.h"
#include "pause_overlay.h"
#include "pipeline_creation.h"
static void compatibilityBind(id e,SEL s,id p){NSDictionary*pass=objc_getAssociatedObject(e,&writerPassKey);id original=p;p=restoreSource([e device],p,pass);if([pass[@"legacyEligible"] boolValue]&&!objc_getAssociatedObject(original,&writerPipelineKey)[@"mesh"]){if(p==original)p=restoreTemplate([e device],p,pass);p=attachmentRepair([e device],p,pass);}if([pass[@"legacyEligible"] boolValue])p=pauseOverlay([e device],p,pass);((void(*)(id,SEL,id))previous(e,s))(e,s,p);}
static void compatibilityEnd(id e,SEL s){((void(*)(id,SEL))previous(e,s))(e,s);objc_setAssociatedObject(e,&writerPassKey,nil,OBJC_ASSOCIATION_RETAIN_NONATOMIC);}
static id compatibilityRender(id cb,SEL s,MTLRenderPassDescriptor*d){
 NSMutableArray*formats=[NSMutableArray array];BOOL relevant=NO,hasColor=NO;
 for(int i=0;i<8;i++){id<MTLTexture>t=d.colorAttachments[i].texture;[formats addObject:@(t.pixelFormat)];hasColor|=t!=nil;if(t&&((t.width>=400&&t.width<=4096&&t.height>=200&&t.height<=2160)||testing))relevant=YES;}
 id e=((id(*)(id,SEL,id))previous(cb,s))(cb,s,d);if(!e)return e;
 if(hasColor){NSDictionary*p=@{@"legacyEligible":@(relevant),@"actualFormats":formats,@"actualDepth":@(d.depthAttachment.texture.pixelFormat),@"actualStencil":@(d.stencilAttachment.texture.pixelFormat)};objc_setAssociatedObject(e,&writerPassKey,p,OBJC_ASSOCIATION_RETAIN_NONATOMIC);Class c=object_getClass(e);hook(c,@selector(setRenderPipelineState:),(IMP)compatibilityBind);hook(c,@selector(endEncoding),(IMP)compatibilityEnd);}else objc_setAssociatedObject(e,&writerPassKey,nil,OBJC_ASSOCIATION_RETAIN_NONATOMIC);
 return e;
}
__attribute__((constructor))static void setup(void){@autoreleasepool{
 BOOL game=NO;for(int i=0;i<*_NSGetArgc();i++)if(strstr((*_NSGetArgv())[i],"ACBlackFlag.exe"))game=YES;
 testing=getenv("BF_COMPAT_TEST")!=NULL;if(!game&&!testing)return;methods=[NSMutableDictionary new];id<MTLDevice>d=MTLCreateSystemDefaultDevice();if(!d){fprintf(stderr,"Black Flag compatibility: Metal device unavailable.\n");exit(78);}sourceInstall();Class c=object_getClass(d);
 hook(c,@selector(newRenderPipelineStateWithMeshDescriptor:options:reflection:error:),(IMP)meshSourceCreate);hook(c,@selector(newRenderPipelineStateWithDescriptor:error:),(IMP)renderPS1);hook(c,@selector(newRenderPipelineStateWithDescriptor:options:reflection:error:),(IMP)renderPS2);hook(c,@selector(newRenderPipelineStateWithDescriptor:completionHandler:),(IMP)renderAsync1);hook(c,@selector(newRenderPipelineStateWithDescriptor:options:completionHandler:),(IMP)renderAsync2);
 id<MTLCommandQueue>q=[d newCommandQueue];id<MTLCommandBuffer>cb=[q commandBuffer];hook(object_getClass(cb),@selector(renderCommandEncoderWithDescriptor:),(IMP)compatibilityRender);[q release];fprintf(stderr,"Black Flag compatibility v4 loaded.\n");
}}
