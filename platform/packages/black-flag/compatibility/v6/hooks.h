// Per-thread caches avoid string allocations and locking on repeated lookups.
// New hooks invalidate inherited lookups on all threads through the epoch.
#include <stdint.h>
typedef struct { Class cls; SEL selector; IMP implementation; uint64_t epoch; } BFHookCache;
static uint64_t hookEpoch = 1;
static __thread BFHookCache previousCache[64], installedCache[64];
static unsigned hookSlot(Class c, SEL s) {
    return (unsigned)(((uintptr_t)c >> 3) ^ ((uintptr_t)sel_getName(s) >> 3)) & 63;
}
static IMP previous(id obj, SEL s) {
    Class cls = object_getClass(obj);
    BFHookCache *entry = &previousCache[hookSlot(cls, s)];
    uint64_t epoch = __atomic_load_n(&hookEpoch, __ATOMIC_ACQUIRE);
    if (entry->epoch == epoch && entry->cls == cls && entry->selector == s)
        return entry->implementation;
    @synchronized(methods) {
        for (Class c = cls; c; c = class_getSuperclass(c)) {
            NSValue *v = methods[[NSString stringWithFormat:@"%p:%s", c, sel_getName(s)]];
            if (v) {
                IMP p = v.pointerValue;
                *entry = (BFHookCache){cls, s, p, __atomic_load_n(&hookEpoch, __ATOMIC_RELAXED)};
                return p;
            }
        }
    }
    abort();
}
static void hook(Class c, SEL s, IMP f) {
    BFHookCache *entry = &installedCache[hookSlot(c, s)];
    uint64_t epoch = __atomic_load_n(&hookEpoch, __ATOMIC_ACQUIRE);
    if (entry->epoch == epoch && entry->cls == c && entry->selector == s && entry->implementation == f)
        return;
    @synchronized(methods) {
        NSString *k = [NSString stringWithFormat:@"%p:%s", c, sel_getName(s)];
        if (!methods[k]) {
            Method m = class_getInstanceMethod(c, s);
            if (!m) return;
            IMP p = method_getImplementation(m);
            if (p == f) {
                for (Class b = class_getSuperclass(c); b; b = class_getSuperclass(b)) {
                    NSValue *v = methods[[NSString stringWithFormat:@"%p:%s", b, sel_getName(s)]];
                    if (v) { p = v.pointerValue; break; }
                }
                if (p == f) abort();
            }
            methods[k] = [NSValue valueWithPointer:p];
            class_addMethod(c, s, p, method_getTypeEncoding(m));
            method_setImplementation(class_getInstanceMethod(c, s), f);
            __atomic_add_fetch(&hookEpoch, 1, __ATOMIC_RELEASE);
        }
        *entry = (BFHookCache){c, s, f, __atomic_load_n(&hookEpoch, __ATOMIC_RELAXED)};
    }
}
