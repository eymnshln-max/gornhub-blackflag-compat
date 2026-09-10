static id targetDescriptor(id<MTLDevice>d,MTLRenderPipelineDescriptor*original){
 MTLRenderPipelineDescriptor*copy=[original copy];
 if([original.fragmentFunction.name isEqual:@"PS_Phoenix"]&&original.rasterizationEnabled&&original.colorAttachments[0].pixelFormat==MTLPixelFormatInvalid){
 NSMutableArray*formats=[NSMutableArray array];for(int i=0;i<8;i++)[formats addObject:@(original.colorAttachments[i].pixelFormat)];
 copy.colorAttachments[0].pixelFormat=MTLPixelFormatRGBA8Unorm;
 event(@"target-format-corrected",@{@"fragment":original.fragmentFunction.name,@"vertex":original.vertexFunction.name?:@"",@"originalFormats":formats,@"newFormat0":@70});}
 return copy;
}
