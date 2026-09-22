// Recover color state from this exact D3DMetal pipeline, never another PSO.
static char sourceFixedKey;static unsigned sourceRepairs;
static BOOL sourceUsable(NSDictionary*s){
 if(!s||[s[@"staticCount"] unsignedIntegerValue]<1||[s[@"staticCount"] unsignedIntegerValue]>8||[s[@"packedFormats"] count]!=8||[s[@"blendBytes"] count]!=8)return NO;
 for(NSNumber*n in s[@"packedFormats"])if(n.unsignedIntegerValue)return NO;
 for(NSUInteger i=0;i<[s[@"staticCount"] unsignedIntegerValue];i++){
  NSArray*b=s[@"blendBytes"][i];if(b.count!=12||[b[0] unsignedIntegerValue]>1||[b[9] unsignedIntegerValue]>15||[b[4] unsignedIntegerValue]>4||[b[7] unsignedIntegerValue]>4)return NO;
  for(NSNumber*j in @[@2,@3,@5,@6])if([b[j.unsignedIntegerValue] unsignedIntegerValue]>18)return NO;
 }return YES;
}
static id restoreSource(id<MTLDevice>dev,id ps,NSDictionary*pass){
 NSDictionary*n=objc_getAssociatedObject(ps,&writerPipelineKey),*s=n[@"sourceState"];MTLRenderPipelineDescriptor*d=objc_getAssociatedObject(ps,&savedDescriptorKey);
 if(!d||!d.rasterizationEnabled||!d.fragmentFunction||!sourceUsable(s)||[pass[@"actualFormats"] count]!=8)return ps;
 for(NSDictionary*c in n[@"original"][@"colors"])if([c[@"format"] unsignedIntegerValue])return ps;
 NSArray*formats=pass[@"actualFormats"];BOOL has=NO;for(NSNumber*f in formats)has|=f.unsignedIntegerValue!=0;if(!has)return ps;
 @synchronized(methods){NSString*k=[formats description];NSMutableDictionary*cache=objc_getAssociatedObject(ps,&sourceFixedKey);if(!cache){cache=[NSMutableDictionary dictionary];objc_setAssociatedObject(ps,&sourceFixedKey,cache,OBJC_ASSOCIATION_RETAIN_NONATOMIC);}if(cache[k])return cache[k]==NSNull.null?ps:cache[k];
 MTLRenderPipelineDescriptor*x=[d copy];NSUInteger count=[s[@"staticCount"] unsignedIntegerValue];
 for(NSUInteger i=0;i<8;i++){MTLRenderPipelineColorAttachmentDescriptor*c=x.colorAttachments[i];c.pixelFormat=[formats[i] unsignedIntegerValue];
  if(i>=count){c.writeMask=MTLColorWriteMaskNone;continue;}
  NSArray*b=s[@"blendBytes"][i];c.blendingEnabled=[b[0] boolValue];c.sourceRGBBlendFactor=[b[2] unsignedIntegerValue];c.destinationRGBBlendFactor=[b[3] unsignedIntegerValue];c.rgbBlendOperation=[b[4] unsignedIntegerValue];c.sourceAlphaBlendFactor=[b[5] unsignedIntegerValue];c.destinationAlphaBlendFactor=[b[6] unsignedIntegerValue];c.alphaBlendOperation=[b[7] unsignedIntegerValue];c.writeMask=[b[9] unsignedIntegerValue];
 }
 NSError*err=nil;id fixed=n[@"mesh"]?[dev newRenderPipelineStateWithMeshDescriptor:(id)x options:0 reflection:nil error:&err]:[dev newRenderPipelineStateWithDescriptor:x error:&err];[x release];if(!fixed){cache[k]=NSNull.null;event(@"source-restore-failed",@{@"error":err.description?:@"",@"sourceChain":n[@"chainID"]?:@0});return ps;}cache[k]=fixed;[fixed release];sourceRepairs++;event(@"source-restored",@{@"count":@(sourceRepairs),@"sourceChain":n[@"chainID"]?:@0,@"owner":s[@"owner"]?:@"",@"fragment":d.fragmentFunction.name?:@"",@"formats":formats});return cache[k];}
}
