// Centered 4% zoom of the Wine presentation pass only; original viewport retained.
static char zoomViewportKey,zoomActiveKey;
static MTLViewport zoomedViewport(MTLViewport v){v.originX-=v.width*0.02;v.originY-=v.height*0.02;v.width*=1.04;v.height*=1.04;return v;}
static void zoomSetViewport(id e,SEL s,MTLViewport v){
 objc_setAssociatedObject(e,&zoomViewportKey,[NSData dataWithBytes:&v length:sizeof(v)],OBJC_ASSOCIATION_RETAIN_NONATOMIC);
 if([objc_getAssociatedObject(e,&zoomActiveKey) boolValue])v=zoomedViewport(v);
 ((void(*)(id,SEL,MTLViewport))previous(e,s))(e,s,v);
}
static void zoomBind(id e,id ps){
 NSDictionary*n=objc_getAssociatedObject(ps,&writerPipelineKey);
 BOOL active=[n[@"vertex"] isEqual:@"simpleVS"]&&[n[@"fragment"] isEqual:@"simple2DFS"];
 BOOL was=[objc_getAssociatedObject(e,&zoomActiveKey) boolValue];
 objc_setAssociatedObject(e,&zoomActiveKey,@(active),OBJC_ASSOCIATION_RETAIN_NONATOMIC);
 NSData*data=objc_getAssociatedObject(e,&zoomViewportKey);
 if(data.length==sizeof(MTLViewport)&&(active||was)){
 MTLViewport v;[data getBytes:&v length:sizeof(v)];if(active)v=zoomedViewport(v);
 ((void(*)(id,SEL,MTLViewport))previous(e,@selector(setViewport:)))(e,@selector(setViewport:),v);
 }
}
static void zoomBegin(id e,MTLRenderPassDescriptor*d){
 id<MTLTexture>t=d.colorAttachments[0].texture;
 MTLViewport v={0,0,MAX(1,t.width>>d.colorAttachments[0].level),MAX(1,t.height>>d.colorAttachments[0].level),0,1};
 objc_setAssociatedObject(e,&zoomViewportKey,[NSData dataWithBytes:&v length:sizeof(v)],OBJC_ASSOCIATION_RETAIN_NONATOMIC);
 objc_setAssociatedObject(e,&zoomActiveKey,@NO,OBJC_ASSOCIATION_RETAIN_NONATOMIC);
 hook(object_getClass(e),@selector(setViewport:),(IMP)zoomSetViewport);
}
