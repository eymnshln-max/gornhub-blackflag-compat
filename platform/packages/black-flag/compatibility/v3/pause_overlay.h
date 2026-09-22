// Workaround, not underlying shader/resource fix. Preserve scene beneath broken overlay.
static char pauseOverlayKey;static unsigned pauseOverlayCount;
static id pauseOverlay(id<MTLDevice>dev,id ps,NSDictionary*pass){
 NSDictionary*n=objc_getAssociatedObject(ps,&writerPipelineKey);if(![n[@"fragment"] isEqual:@"PS_ShadePixel"]||![n[@"vertex"] isEqual:@"VS_ShadeVertex"]||[pass[@"actualDepth"] unsignedIntegerValue]||[pass[@"actualStencil"] unsignedIntegerValue])return ps;
 NSArray*f=pass[@"actualFormats"];if(f.count!=8||([f[0] unsignedIntegerValue]!=70&&[f[0] unsignedIntegerValue]!=115))return ps;for(int i=1;i<8;i++)if([f[i] unsignedIntegerValue])return ps;
 NSDictionary*c=[n[@"colors"] firstObject];if(![c[@"blend"] boolValue]||[c[@"srcRGB"] intValue]!=4||[c[@"dstRGB"] intValue]!=5||[c[@"srcAlpha"] intValue]!=4||[c[@"dstAlpha"] intValue]!=5||[c[@"writeMask"] intValue]!=15)return ps;
 MTLRenderPipelineDescriptor*d=objc_getAssociatedObject(ps,&savedDescriptorKey);if(!d||d.depthAttachmentPixelFormat||d.stencilAttachmentPixelFormat||d.rasterSampleCount!=1)return ps;
 @synchronized(methods){id v=objc_getAssociatedObject(ps,&pauseOverlayKey);if(v)return v==NSNull.null?ps:v;MTLRenderPipelineDescriptor*x=[d copy];x.colorAttachments[0].writeMask=MTLColorWriteMaskNone;NSError*err=nil;v=[dev newRenderPipelineStateWithDescriptor:x error:&err];[x release];objc_setAssociatedObject(ps,&pauseOverlayKey,v?:NSNull.null,OBJC_ASSOCIATION_RETAIN_NONATOMIC);if(!v){event(@"pause-overlay-failed",@{@"error":err.description?:@""});return ps;}event(@"pause-overlay-suppressed",@{@"count":@(++pauseOverlayCount),@"sourceChain":n[@"chainID"]?:@0});[v release];return objc_getAssociatedObject(ps,&pauseOverlayKey);}
}
