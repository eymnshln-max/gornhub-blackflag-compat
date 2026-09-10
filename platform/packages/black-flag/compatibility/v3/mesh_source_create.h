static NSDictionary*meshSourceInfo(MTLMeshRenderPipelineDescriptor*x){
 MTLRenderPipelineDescriptor*v=[MTLRenderPipelineDescriptor new];v.fragmentFunction=x.fragmentFunction;v.rasterizationEnabled=x.rasterizationEnabled;v.rasterSampleCount=x.rasterSampleCount;v.depthAttachmentPixelFormat=x.depthAttachmentPixelFormat;v.stencilAttachmentPixelFormat=x.stencilAttachmentPixelFormat;v.alphaToCoverageEnabled=x.alphaToCoverageEnabled;v.alphaToOneEnabled=x.alphaToOneEnabled;for(int i=0;i<8;i++)v.colorAttachments[i]=x.colorAttachments[i];NSMutableDictionary*n=[renderInfo(v) mutableCopy];[v release];n[@"mesh"]=x.meshFunction.name?:@"";n[@"object"]=x.objectFunction.name?:@"";return [n autorelease];
}
static id meshSourceCreate(id d,SEL s,MTLMeshRenderPipelineDescriptor*x,NSUInteger options,void*reflection,void*err){
 NSMutableDictionary*n=[meshSourceInfo(x) mutableCopy];n[@"original"]=meshSourceInfo(x);n[@"sourceState"]=objc_getAssociatedObject(x.colorAttachments,&sourceStateKey)?:@{};@synchronized(methods){n[@"chainID"]=@(++chainSerial);}
 id p=((id(*)(id,SEL,id,NSUInteger,void*,void*))previous(d,s))(d,s,x,options,reflection,err);renderCreated(p,n);if(p)objc_setAssociatedObject(p,&savedDescriptorKey,[[x copy] autorelease],OBJC_ASSOCIATION_RETAIN_NONATOMIC);[n release];return p;
}
