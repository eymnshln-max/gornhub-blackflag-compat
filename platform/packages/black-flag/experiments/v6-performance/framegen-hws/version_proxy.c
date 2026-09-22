#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <winternl.h>
#include <ddk/d3dkmthk.h>
#include <d3dkmdt.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

typedef NTSTATUS (WINAPI *QueryAdapterInfoFn)(D3DKMT_QUERYADAPTERINFO *);
typedef FARPROC (WINAPI *GetProcAddressFn)(HMODULE, LPCSTR);
static GetProcAddressFn real_GetProcAddress;
static QueryAdapterInfoFn real_QueryAdapterInfo;
static void *dll_notification_cookie;

static void log_line(const char *s)
{
    char path[MAX_PATH];
    DWORD n = GetEnvironmentVariableA("BF_HWS_LOG", path, MAX_PATH);
    if (!n || n >= MAX_PATH) return;
    HANDLE f = CreateFileA(path, FILE_APPEND_DATA, FILE_SHARE_READ | FILE_SHARE_WRITE,
                           NULL, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (f != INVALID_HANDLE_VALUE) {
        DWORD wrote;
        WriteFile(f, s, (DWORD)strlen(s), &wrote, NULL);
        CloseHandle(f);
    }
}

static NTSTATUS WINAPI hooked_QueryAdapterInfo(D3DKMT_QUERYADAPTERINFO *q)
{
    NTSTATUS status = real_QueryAdapterInfo ? real_QueryAdapterInfo(q) : (NTSTATUS)0xC0000002;
    if (q && q->Type == KMTQAITYPE_WDDM_2_7_CAPS && q->pPrivateDriverData &&
        q->PrivateDriverDataSize >= sizeof(D3DKMT_WDDM_2_7_CAPS)) {
        D3DKMT_WDDM_2_7_CAPS *caps = (D3DKMT_WDDM_2_7_CAPS *)q->pPrivateDriverData;
        caps->HwSchSupported = 1;
        caps->HwSchEnabled = 1;
        caps->HwSchEnabledByDefault = 1;
        status = 0;
        log_line("reported WDDM 2.7 HWS supported+enabled\r\n");
    }
    return status;
}

static FARPROC WINAPI hooked_GetProcAddress(HMODULE module, LPCSTR name)
{
    FARPROC result = real_GetProcAddress(module, name);
    if (name && (uintptr_t)name > 0xffff && !strcmp(name, "D3DKMTQueryAdapterInfo")) {
        real_QueryAdapterInfo = (QueryAdapterInfoFn)result;
        log_line("intercepted D3DKMTQueryAdapterInfo lookup\r\n");
        return (FARPROC)hooked_QueryAdapterInfo;
    }
    return result;
}

static BOOL replace_iat_slot(IMAGE_THUNK_DATA64 *slot, FARPROC replacement)
{
    DWORD old;
    if (!VirtualProtect(&slot->u1.Function, sizeof(void *), PAGE_READWRITE, &old)) return FALSE;
    slot->u1.Function = (ULONGLONG)(uintptr_t)replacement;
    VirtualProtect(&slot->u1.Function, sizeof(void *), old, &old);
    FlushInstructionCache(GetCurrentProcess(), &slot->u1.Function, sizeof(void *));
    return TRUE;
}

static unsigned patch_module_iat(void *module)
{
    BYTE *base = (BYTE *)module;
    IMAGE_DOS_HEADER *dos = (IMAGE_DOS_HEADER *)base;
    if (!base || dos->e_magic != IMAGE_DOS_SIGNATURE) return FALSE;
    IMAGE_NT_HEADERS64 *nt = (IMAGE_NT_HEADERS64 *)(base + dos->e_lfanew);
    IMAGE_DATA_DIRECTORY dir = nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT];
    if (!dir.VirtualAddress) return 0;
    IMAGE_IMPORT_DESCRIPTOR *desc = (IMAGE_IMPORT_DESCRIPTOR *)(base + dir.VirtualAddress);
    unsigned patched = 0;
    for (; desc->Name; ++desc) {
        const char *dll = (const char *)(base + desc->Name);
        BOOL kernel = !lstrcmpiA(dll, "KERNEL32.dll") || !lstrcmpiA(dll, "kernelbase.dll");
        BOOL gdi = !lstrcmpiA(dll, "GDI32.dll");
        if (!kernel && !gdi) continue;
        if (!desc->OriginalFirstThunk) continue;
        IMAGE_THUNK_DATA64 *orig = (IMAGE_THUNK_DATA64 *)(base +
            desc->OriginalFirstThunk);
        IMAGE_THUNK_DATA64 *iat = (IMAGE_THUNK_DATA64 *)(base + desc->FirstThunk);
        for (; orig->u1.AddressOfData; ++orig, ++iat) {
            if (IMAGE_SNAP_BY_ORDINAL64(orig->u1.Ordinal)) continue;
            IMAGE_IMPORT_BY_NAME *imp = (IMAGE_IMPORT_BY_NAME *)(base + orig->u1.AddressOfData);
            const char *name = (char *)imp->Name;
            if (kernel && !strcmp(name, "GetProcAddress")) {
                if ((FARPROC)(uintptr_t)iat->u1.Function != (FARPROC)hooked_GetProcAddress) {
                    if (!real_GetProcAddress) real_GetProcAddress = (GetProcAddressFn)(uintptr_t)iat->u1.Function;
                    if (replace_iat_slot(iat, (FARPROC)hooked_GetProcAddress)) ++patched;
                }
            } else if (gdi && !strcmp(name, "D3DKMTQueryAdapterInfo")) {
                if ((FARPROC)(uintptr_t)iat->u1.Function != (FARPROC)hooked_QueryAdapterInfo) {
                    if (!real_QueryAdapterInfo) real_QueryAdapterInfo = (QueryAdapterInfoFn)(uintptr_t)iat->u1.Function;
                    if (replace_iat_slot(iat, (FARPROC)hooked_QueryAdapterInfo)) ++patched;
                }
            }
        }
    }
    if (patched) log_line("patched module import table\r\n");
    return patched;
}

static void CALLBACK dll_loaded(ULONG reason, LDR_DLL_NOTIFICATION_DATA *data, void *context)
{
    (void)context;
    if (reason == LDR_DLL_NOTIFICATION_REASON_LOADED && data && data->Loaded.DllBase)
        patch_module_iat(data->Loaded.DllBase);
}

static void patch_loaded_modules(void)
{
    PPEB peb = NtCurrentTeb()->Peb;
    if (!peb || !peb->LdrData) return;
    LIST_ENTRY *head = &peb->LdrData->InLoadOrderModuleList;
    for (LIST_ENTRY *link = head->Flink; link && link != head; link = link->Flink) {
        LDR_DATA_TABLE_ENTRY *entry = CONTAINING_RECORD(link, LDR_DATA_TABLE_ENTRY, InLoadOrderLinks);
        if (entry->DllBase) patch_module_iat(entry->DllBase);
    }
}

BOOL WINAPI DllMain(HINSTANCE inst, DWORD reason, LPVOID reserved)
{
    if (reason == DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(inst);
        WCHAR name[MAX_PATH];
        GetModuleFileNameW(NULL, name, MAX_PATH);
        WCHAR *leaf = name;
        for (WCHAR *p = name; *p; ++p) if (*p == L'\\') leaf = p + 1;
        if (!lstrcmpiW(leaf, L"ACBlackFlag.exe")) {
            patch_loaded_modules();
            if (LdrRegisterDllNotification(0, dll_loaded, NULL, &dll_notification_cookie) == 0)
                log_line("registered DLL load hook\r\n");
        }
    }
    return TRUE;
}
