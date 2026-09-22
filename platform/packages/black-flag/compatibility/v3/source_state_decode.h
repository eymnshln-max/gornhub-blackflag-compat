#pragma once
#import <Foundation/Foundation.h>
#include <mach/mach.h>
#include <mach/mach_vm.h>
static BOOL sourceRead(uintptr_t a,void*out,size_t n){mach_vm_size_t got=0;return mach_vm_read_overwrite(mach_task_self(),a,n,(mach_vm_address_t)out,&got)==KERN_SUCCESS&&got==n;}
static NSDictionary*sourceDecode(uintptr_t callerStack){uintptr_t owner=0;uint64_t packed=0;unsigned char data[0x300];if(!sourceRead(callerStack+0x28,&owner,8)||!sourceRead(callerStack+0x30,&packed,8)||!owner||!sourceRead(owner+0x70,data,sizeof(data)))return nil;NSMutableArray*blend=[NSMutableArray array],*formats=[NSMutableArray array];for(int i=0;i<8;i++){NSMutableArray*b=[NSMutableArray array];for(int j=0;j<12;j++)[b addObject:@(data[0x258+i*12+j])];[blend addObject:b];[formats addObject:@((packed>>(8*i))&255)];}return @{@"owner":[NSString stringWithFormat:@"%p",(void*)owner],@"staticCount":@(data[0x255]),@"packedFormats":formats,@"blendBytes":blend};}
