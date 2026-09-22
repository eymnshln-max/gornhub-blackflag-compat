static char savedDescriptorKey,repairedVariantsKey;
static unsigned repairedCount,repairFailures;
static id attachmentRepair(id<MTLDevice>device,id p,NSDictionary*pass){
 MTLRenderPipelineDescriptor*d=objc_getAssociatedObject(p,&savedDescriptorKey);if(!d||!d.rasterizationEnabled||!d.fragmentFunction||!pass)return p;
 BOOL any=NO,missing=NO;NSArray*a=pass[@"actualFormats"];if(a.count!=8)return p;
 for(int i=0;i<8;i++){if(d.colorAttachments[i].pixelFormat)any=YES;if([a[i] unsignedIntegerValue]&&d.colorAttachments[i].pixelFormat==0)missing=YES;}
 if(any||!missing)return p;NSString*key=[a componentsJoinedByString:@","];
 @synchronized(methods){NSMutableDictionary*c=objc_getAssociatedObject(p,&repairedVariantsKey);if(!c){c=[NSMutableDictionary dictionary];objc_setAssociatedObject(p,&repairedVariantsKey,c,OBJC_ASSOCIATION_RETAIN_NONATOMIC);}id existing=c[key];if(existing)return existing==NSNull.null?p:existing;
 MTLRenderPipelineDescriptor*copy=[d copy];for(int i=0;i<8;i++)copy.colorAttachments[i].pixelFormat=[a[i] unsignedIntegerValue];
 NSError*error=nil;id fixed=[device newRenderPipelineStateWithDescriptor:copy error:&error];[copy release];if(fixed){c[key]=fixed;[fixed release];repairedCount++;event(@"attachment-repair",@{@"vertex":d.vertexFunction.name?:@"",@"fragment":d.fragmentFunction.name?:@"",@"formats":a,@"number":@(repairedCount)});return c[key];}
 c[key]=NSNull.null;repairFailures++;event(@"attachment-repair-failed",@{@"fragment":d.fragmentFunction.name?:@"",@"formats":a,@"error":error.description?:@""});return p;
 }
}
