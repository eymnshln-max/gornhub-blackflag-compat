#include "compatibility.m"
// Run with argv ACBlackFlag.exe to exercise the production size filter.
// BF_COMPAT_TEST must be absent: these are actual-size GPU tests.
int main(int argc,char**argv){@autoreleasepool{
 if(testing||!methods){fprintf(stderr,"Production hook activation required\n");return 10;}
 id<MTLDevice>d=MTLCreateSystemDefaultDevice();NSError*err=nil;
 NSString*src=@"#include <metal_stdlib>\nusing namespace metal;vertex float4 VS_ShadeVertex(uint i[[vertex_id]]){float2 p[3]={float2(-1,-1),float2(3,-1),float2(-1,3)};return float4(p[i],0,1);}fragment float4 PS_ShadePixel(){return float4(1,0,1,1);}";
 id<MTLLibrary>l=[d newLibraryWithSource:src options:nil error:&err];if(!l)return 11;
 NSUInteger sizes[][2]={{1512,945},{2560,1600},{3024,1964}};
 for(int sz=0;sz<3;sz++)for(int hdr=0;hdr<2;hdr++)for(int negative=0;negative<2;negative++){@autoreleasepool{
  NSUInteger w=sizes[sz][0],h=sizes[sz][1],fmt=hdr?115:70;
  MTLRenderPipelineDescriptor*pd=[MTLRenderPipelineDescriptor new];pd.vertexFunction=[l newFunctionWithName:@"VS_ShadeVertex"];pd.fragmentFunction=[l newFunctionWithName:@"PS_ShadePixel"];
  pd.colorAttachments[0].pixelFormat=fmt;pd.colorAttachments[0].blendingEnabled=!negative;
  pd.colorAttachments[0].sourceRGBBlendFactor=4;pd.colorAttachments[0].destinationRGBBlendFactor=5;pd.colorAttachments[0].sourceAlphaBlendFactor=4;pd.colorAttachments[0].destinationAlphaBlendFactor=5;
  id ps=[d newRenderPipelineStateWithDescriptor:pd error:&err];if(!ps)return 12;
  MTLTextureDescriptor*td=[MTLTextureDescriptor texture2DDescriptorWithPixelFormat:fmt width:w height:h mipmapped:NO];td.storageMode=MTLStorageModeShared;td.usage=MTLTextureUsageRenderTarget;
  id<MTLTexture>t=[d newTextureWithDescriptor:td];id<MTLCommandQueue>q=[d newCommandQueue];id<MTLCommandBuffer>cb=[q commandBuffer];
  MTLRenderPassDescriptor*rp=[MTLRenderPassDescriptor renderPassDescriptor];rp.colorAttachments[0].texture=t;rp.colorAttachments[0].loadAction=MTLLoadActionClear;rp.colorAttachments[0].storeAction=MTLStoreActionStore;rp.colorAttachments[0].clearColor=MTLClearColorMake(0,1,0,1);
  id<MTLRenderCommandEncoder>e=[cb renderCommandEncoderWithDescriptor:rp];if(!objc_getAssociatedObject(e,&writerPassKey))return 13;
  [e setRenderPipelineState:ps];[e drawPrimitives:MTLPrimitiveTypeTriangle vertexStart:0 vertexCount:3];[e endEncoding];[cb commit];[cb waitUntilCompleted];if(cb.status!=MTLCommandBufferStatusCompleted)return 14;
  size_t row=w*(hdr?8:4);void*raw=malloc(row*h);if(!raw)return 15;
  [t getBytes:raw bytesPerRow:row fromRegion:MTLRegionMake2D(0,0,w,h) mipmapLevel:0];
  for(size_t i=0;i<w*h;i++)for(int c=0;c<4;c++){float expected=c==3?1:(negative?(c==1?0:1):(c==1?1:0));float got=hdr?(float)((_Float16*)raw)[i*4+c]:(float)((uint8_t*)raw)[i*4+c]/255.0f;if(got!=expected){free(raw);return 16;}}
  free(raw);[t release];[q release];[ps release];[pd release];printf("PASS %lux%lu %s %s (%lu pixels)\n",w,h,hdr?"HDR":"SDR",negative?"negative":"matching",w*h);
 }}
 return 0;
}}
