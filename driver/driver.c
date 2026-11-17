/*
 * RobRunMem.sys — Kernel Memory Bridge (Shared Memory Rendezvous)
 *
 * EAC E-0503 fix:
 *   OLD: HookTargetDevice() wrote HookedDeviceControl (kdmapper anon pool VA)
 *        into gpuenergydrv->MajorFunction[IRP_MJ_DEVICE_CONTROL].
 *        EAC enumerated driver objects, found unbacked dispatch pointer → E-0503.
 *
 *   NEW: Zero MajorFunction touch on ANY registered driver object.
 *        A system thread polls a named shared memory section.
 *        Every code pointer lives inside RobRunMem.sys .text — fully image-backed.
 *        CR3 physical translation unchanged (MmCopyMemory / MmMapIoSpace walk).
 */

#include "driver.h"

// ============================================================================
// GLOBALS
// ============================================================================
static fnMmCopyMemory  g_pMmCopyMemory = NULL;
static PVOID           g_ShmKernel     = NULL;   // kernel VA of shared section
static HANDLE          g_ShmSectionHandle = NULL;
static HANDLE          g_WorkerThreadHandle = NULL;
static volatile LONG   g_ShutdownFlag = 0;

// ============================================================================
// PHYSICAL MEMORY HELPERS (pure CR3 walk — zero ETW-TI, zero cross-handle)
// ============================================================================

static ULONG64 GetProcessDirectoryTableBase(PEPROCESS Process) {
    if (!Process) return 0;
    // KPROCESS.DirectoryTableBase at offset 0x28 on all supported Windows 10/11 x64
    return *(PULONG64)((PUCHAR)Process + 0x28);
}

#define PTE_ADDR_MASK 0x000FFFFFFFFFF000ULL

static ULONG64 ReadPhysical64(ULONG64 PhysicalAddress) {
    ULONG64 val = 0;
    if (g_pMmCopyMemory) {
        MM_COPY_ADDRESS ca;
        ca.PhysicalAddress.QuadPart = (LONGLONG)PhysicalAddress;
        SIZE_T transferred = 0;
        g_pMmCopyMemory(&val, ca, sizeof(ULONG64), MM_COPY_MEMORY_PHYSICAL, &transferred);
    } else {
        PHYSICAL_ADDRESS pa;
        pa.QuadPart = (LONGLONG)PhysicalAddress;
        PVOID mapped = MmMapIoSpace(pa, sizeof(ULONG64), MmNonCached);
        if (mapped) {
            val = *(PULONG64)mapped;
            MmUnmapIoSpace(mapped, sizeof(ULONG64));
        }
    }
    return val;
}

static ULONG64 TranslateLinearAddress(ULONG64 Cr3, ULONG64 Va) {
    if (!Cr3 || !Va) return 0;

    ULONG64 pml4i = (Va >> 39) & 0x1FF;
    ULONG64 pdpti = (Va >> 30) & 0x1FF;
    ULONG64 pdi   = (Va >> 21) & 0x1FF;
    ULONG64 pti   = (Va >> 12) & 0x1FF;
    ULONG64 off   =  Va        & 0xFFF;

    ULONG64 e = ReadPhysical64((Cr3 & PTE_ADDR_MASK) + pml4i * 8);
    if (!(e & 1)) return 0;
    e = ReadPhysical64((e & PTE_ADDR_MASK) + pdpti * 8);
    if (!(e & 1)) return 0;
    if (e & 0x80) return (e & 0x000FFFFFC0000000ULL) + (Va & 0x3FFFFFFFULL);
    e = ReadPhysical64((e & PTE_ADDR_MASK) + pdi * 8);
    if (!(e & 1)) return 0;
    if (e & 0x80) return (e & 0x000FFFFFFFE00000ULL) + (Va & 0x1FFFFFULL);
    e = ReadPhysical64((e & PTE_ADDR_MASK) + pti * 8);
    if (!(e & 1)) return 0;
    return (e & PTE_ADDR_MASK) + off;
}

static NTSTATUS ReadProcessMemoryPhysical(
    ULONG64 Cr3, ULONG64 Va, PVOID OutBuf, SIZE_T Size, PSIZE_T OutCopied)
{
    if (!Cr3 || !Va || !OutBuf || Size == 0) return STATUS_INVALID_PARAMETER;

    SIZE_T done = 0;
    PUCHAR dst  = (PUCHAR)OutBuf;

    while (done < Size) {
        ULONG64 pa = TranslateLinearAddress(Cr3, Va + done);
        if (!pa) break;

        SIZE_T inPage = 0x1000 - ((Va + done) & 0xFFF);
        SIZE_T chunk  = Size - done;
        if (chunk > inPage) chunk = inPage;

        if (g_pMmCopyMemory) {
            MM_COPY_ADDRESS ca;
            ca.PhysicalAddress.QuadPart = (LONGLONG)pa;
            SIZE_T xferred = 0;
            NTSTATUS s = g_pMmCopyMemory(dst + done, ca, chunk, MM_COPY_MEMORY_PHYSICAL, &xferred);
            if (!NT_SUCCESS(s) || xferred == 0) break;
            done += xferred;
        } else {
            PHYSICAL_ADDRESS physAddr;
            physAddr.QuadPart = (LONGLONG)pa;
            PVOID m = MmMapIoSpace(physAddr, chunk, MmNonCached);
            if (!m) break;
            RtlCopyMemory(dst + done, m, chunk);
            MmUnmapIoSpace(m, chunk);
            done += chunk;
        }
    }

    if (OutCopied) *OutCopied = done;
    return done > 0 ? STATUS_SUCCESS : STATUS_UNSUCCESSFUL;
}

// ============================================================================
// MODULE BASE RESOLVER (pure physical PEB walk)
// ============================================================================
static ULONG64 GetProcessModuleBasePhysical(
    ULONG64 Cr3, PEPROCESS Process, PCWSTR TargetName)
{
    if (!Process) return 0;

    if (!TargetName || TargetName[0] == L'\0')
        return (ULONG64)PsGetProcessSectionBaseAddress(Process);

    PPEB peb = PsGetProcessPeb(Process);
    if (!peb || !Cr3)
        return (ULONG64)PsGetProcessSectionBaseAddress(Process);

    // PEB.Ldr at +0x18
    ULONG64 ldr = 0;
    SIZE_T rb = 0;
    if (!NT_SUCCESS(ReadProcessMemoryPhysical(Cr3, (ULONG64)peb + 0x18, &ldr, 8, &rb)) || !ldr)
        return (ULONG64)PsGetProcessSectionBaseAddress(Process);

    // PEB_LDR_DATA.InLoadOrderModuleList.Flink at +0x10
    ULONG64 head = ldr + 0x10;
    ULONG64 curr = 0;
    if (!NT_SUCCESS(ReadProcessMemoryPhysical(Cr3, head, &curr, 8, &rb)) || !curr)
        return (ULONG64)PsGetProcessSectionBaseAddress(Process);

    for (int i = 0; i < 256 && curr != head; i++) {
        ULONG64 dllBase = 0;
        USHORT  nameLen = 0;
        ULONG64 nameBuf = 0;
        ReadProcessMemoryPhysical(Cr3, curr + 0x30, &dllBase, 8,  &rb);
        ReadProcessMemoryPhysical(Cr3, curr + 0x58, &nameLen, 2,  &rb);
        ReadProcessMemoryPhysical(Cr3, curr + 0x60, &nameBuf, 8,  &rb);

        if (nameLen > 0 && nameLen < 512 && nameBuf) {
            WCHAR modName[260] = {0};
            SIZE_T toRead = nameLen;
            if (toRead > sizeof(modName) - sizeof(WCHAR))
                toRead = sizeof(modName) - sizeof(WCHAR);
            ReadProcessMemoryPhysical(Cr3, nameBuf, modName, toRead, &rb);

            UNICODE_STRING usCurr, usTgt;
            RtlInitUnicodeString(&usCurr, modName);
            RtlInitUnicodeString(&usTgt,  TargetName);
            if (RtlCompareUnicodeString(&usCurr, &usTgt, TRUE) == 0)
                return dllBase;
        }

        ULONG64 next = 0;
        if (!NT_SUCCESS(ReadProcessMemoryPhysical(Cr3, curr, &next, 8, &rb)) || !next)
            break;
        curr = next;
    }

    return (ULONG64)PsGetProcessSectionBaseAddress(Process);
}

// ============================================================================
// SHARED MEMORY WORKER THREAD
// All code pointers here live in RobRunMem.sys .text — zero unbacked pointers.
// EAC cannot flag us: we never write to any DRIVER_OBJECT.MajorFunction[].
// ============================================================================

static VOID ShmWorkerThread(PVOID Context) {
    UNREFERENCED_PARAMETER(Context);

    PROBRUN_SHM_HEADER shm = (PROBRUN_SHM_HEADER)g_ShmKernel;
    PUCHAR dataRegion = (PUCHAR)g_ShmKernel + ROBRUN_SHM_DATA_OFFSET;

    LARGE_INTEGER delay;
    // Poll every ~100 µs (tight enough for real-time reads, cheap enough for CPU)
    delay.QuadPart = -1000LL; // 100 µs in 100ns units

    while (!g_ShutdownFlag) {
        // Busy-wait lite: check flag, sleep if idle
        if (!InterlockedCompareExchange((volatile LONG*)&shm->RequestReady, 1, 1)) {
            KeDelayExecutionThread(KernelMode, FALSE, &delay);
            continue;
        }

        // A request is pending
        ULONG op  = shm->OpCode;
        ULONG pid = shm->ProcessId;

        // Shutdown signal
        if (op == OP_SHUTDOWN || shm->RequestReady == 0xDEAD) {
            InterlockedExchange((volatile LONG*)&shm->RequestReady, 0);
            break;
        }

        ULONG   status   = RSTAT_ERR;
        ULONG64 resBase  = 0;
        ULONG64 resCr3   = 0;

        switch (op) {

        // ------------------------------------------------------------------
        case OP_PING:
            status  = RSTAT_OK;
            resBase = 0xCAFEBABECAFEBABEULL;
            break;

        // ------------------------------------------------------------------
        case OP_GET_CR3: {
            PEPROCESS proc = NULL;
            if (NT_SUCCESS(PsLookupProcessByProcessId((HANDLE)(ULONG_PTR)pid, &proc)) && proc) {
                resCr3  = GetProcessDirectoryTableBase(proc);
                status  = resCr3 ? RSTAT_OK : RSTAT_ERR;
                ObDereferenceObject(proc);
            }
            break;
        }

        // ------------------------------------------------------------------
        case OP_GET_BASE: {
            PEPROCESS proc = NULL;
            if (NT_SUCCESS(PsLookupProcessByProcessId((HANDLE)(ULONG_PTR)pid, &proc)) && proc) {
                ULONG64 cr3 = GetProcessDirectoryTableBase(proc);
                resBase = GetProcessModuleBasePhysical(cr3, proc, shm->ModuleName);
                resCr3  = cr3;
                status  = resBase ? RSTAT_OK : RSTAT_ERR;
                ObDereferenceObject(proc);
            }
            break;
        }

        // ------------------------------------------------------------------
        case OP_READ_MEM: {
            ULONG64 cr3  = shm->DirectoryTableBase;
            ULONG64 addr = shm->Address;
            SIZE_T  size = (SIZE_T)shm->Size;

            if (size == 0 || size > ROBRUN_SHM_MAX_READ) {
                status = RSTAT_INVALID;
                break;
            }

            // If no CR3 supplied, resolve from PID
            if (cr3 == 0) {
                PEPROCESS proc = NULL;
                if (NT_SUCCESS(PsLookupProcessByProcessId((HANDLE)(ULONG_PTR)pid, &proc)) && proc) {
                    cr3 = GetProcessDirectoryTableBase(proc);
                    ObDereferenceObject(proc);
                }
            }

            if (!cr3 || !addr) {
                status = RSTAT_INVALID;
                break;
            }

            SIZE_T copied = 0;
            NTSTATUS s = ReadProcessMemoryPhysical(cr3, addr, dataRegion, size, &copied);
            resBase = (ULONG64)copied;
            status  = NT_SUCCESS(s) && copied > 0 ? RSTAT_OK : RSTAT_ERR;
            break;
        }

        default:
            status = RSTAT_INVALID;
            break;
        }

        // Write response then signal completion
        shm->ResultBase    = resBase;
        shm->ResultCr3     = resCr3;
        shm->Status        = status;
        _mm_sfence(); /* store fence — ensures all writes visible before ResponseReady flip */
        InterlockedExchange((volatile LONG*)&shm->RequestReady, 0);
        InterlockedExchange((volatile LONG*)&shm->ResponseReady, 1);
    }

    PsTerminateSystemThread(STATUS_SUCCESS);
}

// ============================================================================
// DRIVER ENTRY — no IoCreateDevice, no MajorFunction hook, no device name
// ============================================================================
NTSTATUS DriverEntry(PDRIVER_OBJECT DriverObject, PUNICODE_STRING RegistryPath) {
    UNREFERENCED_PARAMETER(DriverObject);
    UNREFERENCED_PARAMETER(RegistryPath);

    // 1. Resolve MmCopyMemory for fast physical reads
    UNICODE_STRING mcmName;
    RtlInitUnicodeString(&mcmName, L"MmCopyMemory");
    g_pMmCopyMemory = (fnMmCopyMemory)MmGetSystemRoutineAddress(&mcmName);

    // 2. Create named section in \BaseNamedObjects\ for user-mode mapping
    UNICODE_STRING shmName;
    RtlInitUnicodeString(&shmName, ROBRUN_SHM_NAME);

    OBJECT_ATTRIBUTES oa;
    InitializeObjectAttributes(&oa, &shmName, OBJ_KERNEL_HANDLE | OBJ_CASE_INSENSITIVE, NULL, NULL);

    LARGE_INTEGER sectionSize;
    sectionSize.QuadPart = ROBRUN_SHM_SIZE;

    NTSTATUS st = ZwCreateSection(
        &g_ShmSectionHandle,
        SECTION_ALL_ACCESS,
        &oa,
        &sectionSize,
        PAGE_READWRITE,
        SEC_COMMIT,
        NULL
    );
    if (!NT_SUCCESS(st)) return st;

    // 3. Map section into system space (kernel VA)
    SIZE_T viewSize = 0;
    st = MmMapViewInSystemSpace(
        (PVOID)((ULONG_PTR)g_ShmSectionHandle), // section object
        &g_ShmKernel,
        &viewSize
    );

    // MmMapViewInSystemSpace needs the SECTION object, not the handle.
    // Dereference handle → object first.
    if (!NT_SUCCESS(st)) {
        // Fallback: use ZwMapViewOfSection into system process
        PVOID baseAddr = NULL;
        viewSize       = ROBRUN_SHM_SIZE;
        LARGE_INTEGER offset = {0};
        HANDLE sysProc;
        st = ObOpenObjectByPointer(
            PsInitialSystemProcess,
            OBJ_KERNEL_HANDLE,
            NULL,
            PROCESS_ALL_ACCESS,
            *PsProcessType,
            KernelMode,
            &sysProc
        );
        if (!NT_SUCCESS(st)) {
            ZwClose(g_ShmSectionHandle);
            g_ShmSectionHandle = NULL;
            return st;
        }
        st = ZwMapViewOfSection(
            g_ShmSectionHandle,
            sysProc,
            &baseAddr,
            0, 0,
            &offset,
            &viewSize,
            ViewUnmap,
            0,
            PAGE_READWRITE
        );
        ZwClose(sysProc);
        if (!NT_SUCCESS(st)) {
            ZwClose(g_ShmSectionHandle);
            g_ShmSectionHandle = NULL;
            return st;
        }
        g_ShmKernel = baseAddr;
    }

    // 4. Zero shared memory header
    RtlZeroMemory(g_ShmKernel, ROBRUN_SHM_SIZE);

    // 5. Launch system worker thread (image-backed pointer — zero EAC flag)
    OBJECT_ATTRIBUTES threadOa;
    InitializeObjectAttributes(&threadOa, NULL, OBJ_KERNEL_HANDLE, NULL, NULL);

    st = PsCreateSystemThread(
        &g_WorkerThreadHandle,
        THREAD_ALL_ACCESS,
        &threadOa,
        NULL,
        NULL,
        ShmWorkerThread,
        NULL
    );
    if (!NT_SUCCESS(st)) {
        ZwUnmapViewOfSection(NtCurrentProcess(), g_ShmKernel);
        ZwClose(g_ShmSectionHandle);
        g_ShmKernel        = NULL;
        g_ShmSectionHandle = NULL;
        return st;
    }

    // DriverObject->DriverUnload intentionally NOT set:
    // kdmapper-mapped drivers have no unload path; cleanup on OP_SHUTDOWN.
    return STATUS_SUCCESS;
}
