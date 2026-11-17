#include "driver.h"

static fnMmCopyMemory g_pMmCopyMemory = NULL;
static PDRIVER_DISPATCH g_OriginalDeviceControl = NULL;
static PDRIVER_OBJECT g_pHookedDriver = NULL;

ULONG64 GetProcessDirectoryTableBase(PEPROCESS Process) {
    if (!Process) return 0;
    PUCHAR kproc = (PUCHAR)Process;
    return *(PULONG64)(kproc + 0x28);
}

// -----------------------------------------------------------------------------
// HARDWARE-LEVEL PHYSICAL MEMORY TRANSLATION (ZERO ETW-TI / ZERO CROSS-HANDLE)
// -----------------------------------------------------------------------------
static ULONG64 ReadPhysical64(ULONG64 PhysicalAddress) {
    ULONG64 val = 0;
    if (g_pMmCopyMemory) {
        MM_COPY_ADDRESS copyAddr;
        copyAddr.PhysicalAddress.QuadPart = (LONGLONG)PhysicalAddress;
        SIZE_T bytesTransferred = 0;
        g_pMmCopyMemory(&val, copyAddr, sizeof(ULONG64), MM_COPY_MEMORY_PHYSICAL, &bytesTransferred);
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

static ULONG64 TranslateLinearAddress(ULONG64 Cr3, ULONG64 VirtualAddress) {
    if (!Cr3 || !VirtualAddress) return 0;
    
    #define PTE_ADDR_MASK 0x000FFFFFFFFFF000ULL

    ULONG64 pml4Index = (VirtualAddress >> 39) & 0x1FF;
    ULONG64 pdptIndex = (VirtualAddress >> 30) & 0x1FF;
    ULONG64 pdIndex   = (VirtualAddress >> 21) & 0x1FF;
    ULONG64 ptIndex   = (VirtualAddress >> 12) & 0x1FF;
    ULONG64 offset    = VirtualAddress & 0xFFF;

    // 1. PML4 Entry
    ULONG64 pml4Entry = ReadPhysical64((Cr3 & PTE_ADDR_MASK) + pml4Index * 8);
    if (!(pml4Entry & 1)) return 0;

    // 2. PDPT Entry
    ULONG64 pdptEntry = ReadPhysical64((pml4Entry & PTE_ADDR_MASK) + pdptIndex * 8);
    if (!(pdptEntry & 1)) return 0;
    if (pdptEntry & 0x80) { // 1GB Large Page
        return (pdptEntry & 0x000FFFFFC0000000ULL) + (VirtualAddress & 0x3FFFFFFFULL);
    }

    // 3. PD Entry
    ULONG64 pdEntry = ReadPhysical64((pdptEntry & PTE_ADDR_MASK) + pdIndex * 8);
    if (!(pdEntry & 1)) return 0;
    if (pdEntry & 0x80) { // 2MB Large Page
        return (pdEntry & 0x000FFFFFFFE00000ULL) + (VirtualAddress & 0x1FFFFFULL);
    }

    // 4. Page Table Entry (4KB)
    ULONG64 ptEntry = ReadPhysical64((pdEntry & PTE_ADDR_MASK) + ptIndex * 8);
    if (!(ptEntry & 1)) return 0;

    return (ptEntry & PTE_ADDR_MASK) + offset;
}

static NTSTATUS ReadProcessMemoryPhysical(ULONG64 Cr3, ULONG64 VirtualAddress, PVOID OutBuffer, SIZE_T Size, PSIZE_T OutCopied) {
    if (!Cr3 || !VirtualAddress || !OutBuffer || Size == 0) return STATUS_INVALID_PARAMETER;
    
    SIZE_T totalCopied = 0;
    PUCHAR dest = (PUCHAR)OutBuffer;
    ULONG64 currVa = VirtualAddress;
    
    while (totalCopied < Size) {
        ULONG64 pa = TranslateLinearAddress(Cr3, currVa);
        if (!pa) break;
        
        SIZE_T bytesInPage = 0x1000 - (currVa & 0xFFF);
        SIZE_T bytesToCopy = Size - totalCopied;
        if (bytesToCopy > bytesInPage) bytesToCopy = bytesInPage;
        
        if (g_pMmCopyMemory) {
            MM_COPY_ADDRESS copyAddr;
            copyAddr.PhysicalAddress.QuadPart = (LONGLONG)pa;
            SIZE_T transferred = 0;
            NTSTATUS st = g_pMmCopyMemory(dest + totalCopied, copyAddr, bytesToCopy, MM_COPY_MEMORY_PHYSICAL, &transferred);
            if (!NT_SUCCESS(st) || transferred == 0) break;
            totalCopied += transferred;
            currVa += transferred;
        } else {
            PHYSICAL_ADDRESS physAddr;
            physAddr.QuadPart = (LONGLONG)pa;
            PVOID mapped = MmMapIoSpace(physAddr, bytesToCopy, MmNonCached);
            if (!mapped) break;
            RtlCopyMemory(dest + totalCopied, mapped, bytesToCopy);
            MmUnmapIoSpace(mapped, bytesToCopy);
            totalCopied += bytesToCopy;
            currVa += bytesToCopy;
        }
    }
    
    if (OutCopied) *OutCopied = totalCopied;
    return totalCopied > 0 ? STATUS_SUCCESS : STATUS_UNSUCCESSFUL;
}

// -----------------------------------------------------------------------------
// MODULE BASE RESOLVER VIA PEB (PHYSICAL MEMORY SAFE)
// -----------------------------------------------------------------------------
static ULONG64 GetProcessModuleBasePhysical(ULONG64 Cr3, PEPROCESS Process, PCWSTR TargetName) {
    if (!Process) return 0;

    if (!TargetName || TargetName[0] == L'\0') {
        return (ULONG64)PsGetProcessSectionBaseAddress(Process);
    }

    PPEB pPeb = PsGetProcessPeb(Process);
    if (!pPeb || !Cr3) {
        return (ULONG64)PsGetProcessSectionBaseAddress(Process);
    }

    ULONG64 pLdr = 0;
    SIZE_T copied = 0;
    if (!NT_SUCCESS(ReadProcessMemoryPhysical(Cr3, (ULONG64)pPeb + 0x18, &pLdr, sizeof(ULONG64), &copied)) || !pLdr) {
        return (ULONG64)PsGetProcessSectionBaseAddress(Process);
    }

    ULONG64 listHead = pLdr + 0x10; // InLoadOrderModuleList
    ULONG64 current = 0;
    if (!NT_SUCCESS(ReadProcessMemoryPhysical(Cr3, listHead, &current, sizeof(ULONG64), &copied)) || !current) {
        return (ULONG64)PsGetProcessSectionBaseAddress(Process);
    }

    for (int i = 0; i < 256 && current != listHead; i++) {
        ULONG64 dllBase = 0;
        USHORT nameLength = 0;
        ULONG64 pBuffer = 0;

        ReadProcessMemoryPhysical(Cr3, current + 0x30, &dllBase, sizeof(ULONG64), &copied);
        ReadProcessMemoryPhysical(Cr3, current + 0x58, &nameLength, sizeof(USHORT), &copied);
        ReadProcessMemoryPhysical(Cr3, current + 0x60, &pBuffer, sizeof(ULONG64), &copied);

        if (pBuffer && nameLength > 0 && nameLength < 520) {
            WCHAR modName[260];
            RtlZeroMemory(modName, sizeof(modName));
            ReadProcessMemoryPhysical(Cr3, pBuffer, modName, nameLength, &copied);
            
            UNICODE_STRING uCurrent, uTarget;
            RtlInitUnicodeString(&uCurrent, modName);
            RtlInitUnicodeString(&uTarget, TargetName);
            if (RtlCompareUnicodeString(&uCurrent, &uTarget, TRUE) == 0) {
                return dllBase;
            }
        }

        ULONG64 next = 0;
        if (!NT_SUCCESS(ReadProcessMemoryPhysical(Cr3, current, &next, sizeof(ULONG64), &copied)) || !next) {
            break;
        }
        current = next;
    }

    return (ULONG64)PsGetProcessSectionBaseAddress(Process);
}

// -----------------------------------------------------------------------------
// STEALTH IRP DISPATCH ROUTINE (ZERO BSOD - PURE BUFFERED I/O)
// -----------------------------------------------------------------------------
static NTSTATUS HookedDeviceControl(PDEVICE_OBJECT DeviceObject, PIRP Irp) {
    PIO_STACK_LOCATION irpSp = IoGetCurrentIrpStackLocation(Irp);
    ULONG ioctlCode = irpSp->Parameters.DeviceIoControl.IoControlCode;

    // If it's not our IOCTL, forward immediately to original driver handler
    if ((ioctlCode & 0x80000000) == 0) {
        if (g_OriginalDeviceControl) {
            return g_OriginalDeviceControl(DeviceObject, Irp);
        }
        Irp->IoStatus.Status = STATUS_INVALID_DEVICE_REQUEST;
        IoCompleteRequest(Irp, IO_NO_INCREMENT);
        return STATUS_INVALID_DEVICE_REQUEST;
    }

    NTSTATUS status = STATUS_SUCCESS;
    ULONG_PTR bytesReturned = 0;
    PVOID buffer = Irp->AssociatedIrp.SystemBuffer;
    ULONG inLength = irpSp->Parameters.DeviceIoControl.InputBufferLength;
    ULONG outLength = irpSp->Parameters.DeviceIoControl.OutputBufferLength;

    switch (ioctlCode) {
        case IOCTL_ROBRUN_READ_MEM: {
            if (inLength < sizeof(ROBRUN_READ_REQUEST) || !buffer) {
                status = STATUS_INVALID_PARAMETER;
                break;
            }
            PROBRUN_READ_REQUEST req = (PROBRUN_READ_REQUEST)buffer;
            if (req->Size == 0 || !req->Response) {
                status = STATUS_INVALID_PARAMETER;
                break;
            }
            SIZE_T copied = 0;
            status = ReadProcessMemoryPhysical(req->DirectoryTableBase, req->Address, req->Response, req->Size, &copied);
            bytesReturned = copied;
            break;
        }

        case IOCTL_ROBRUN_GET_BASE: {
            if (inLength < sizeof(ROBRUN_MODULE_REQUEST) || outLength < sizeof(ROBRUN_MODULE_REQUEST) || !buffer) {
                status = STATUS_INVALID_PARAMETER;
                break;
            }
            PROBRUN_MODULE_REQUEST req = (PROBRUN_MODULE_REQUEST)buffer;
            PEPROCESS targetProcess = NULL;
            status = PsLookupProcessByProcessId((HANDLE)(ULONG_PTR)req->ProcessId, &targetProcess);
            if (NT_SUCCESS(status) && targetProcess) {
                ULONG64 cr3 = GetProcessDirectoryTableBase(targetProcess);
                req->BaseAddress = GetProcessModuleBasePhysical(cr3, targetProcess, req->ModuleName);
                bytesReturned = sizeof(ROBRUN_MODULE_REQUEST);
                ObDereferenceObject(targetProcess);
                status = STATUS_SUCCESS;
            }
            break;
        }

        case IOCTL_ROBRUN_GET_CR3: {
            if (inLength < sizeof(ROBRUN_CR3_REQUEST) || outLength < sizeof(ROBRUN_CR3_REQUEST) || !buffer) {
                status = STATUS_INVALID_PARAMETER;
                break;
            }
            PROBRUN_CR3_REQUEST req = (PROBRUN_CR3_REQUEST)buffer;
            PEPROCESS targetProcess = NULL;
            status = PsLookupProcessByProcessId((HANDLE)(ULONG_PTR)req->ProcessId, &targetProcess);
            if (NT_SUCCESS(status) && targetProcess) {
                req->DirectoryTableBase = GetProcessDirectoryTableBase(targetProcess);
                bytesReturned = sizeof(ROBRUN_CR3_REQUEST);
                ObDereferenceObject(targetProcess);
                status = STATUS_SUCCESS;
            }
            break;
        }

        case IOCTL_ROBRUN_UNHOOK: {
            if (g_pHookedDriver && g_OriginalDeviceControl) {
                InterlockedExchangePointer(
                    (PVOID*)&g_pHookedDriver->MajorFunction[IRP_MJ_DEVICE_CONTROL],
                    (PVOID)g_OriginalDeviceControl
                );
            }
            status = STATUS_SUCCESS;
            bytesReturned = 0;
            break;
        }

        default:
            status = STATUS_INVALID_PARAMETER;
            break;
    }

    Irp->IoStatus.Status = status;
    Irp->IoStatus.Information = bytesReturned;
    IoCompleteRequest(Irp, IO_NO_INCREMENT);
    return status;
}

// -----------------------------------------------------------------------------
// HELPER: HOOK DEVICE QUA IoGetDeviceObjectPointer (STEALTH IRP DISPATCH SWAP)
// -----------------------------------------------------------------------------
static NTSTATUS HookTargetDevice(PCWSTR DevicePath, ACCESS_MASK DesiredAccess) {
    UNICODE_STRING devName;
    RtlInitUnicodeString(&devName, DevicePath);
    PFILE_OBJECT fileObj = NULL;
    PDEVICE_OBJECT devObj = NULL;

    NTSTATUS st = IoGetDeviceObjectPointer(&devName, DesiredAccess, &fileObj, &devObj);
    if (NT_SUCCESS(st) && devObj && devObj->DriverObject) {
        PDRIVER_OBJECT pDriver = devObj->DriverObject;
        g_pHookedDriver = pDriver;
        PVOID oldDispatch = InterlockedExchangePointer(
            (PVOID*)&pDriver->MajorFunction[IRP_MJ_DEVICE_CONTROL],
            (PVOID)HookedDeviceControl
        );
        if (!g_OriginalDeviceControl) {
            g_OriginalDeviceControl = (PDRIVER_DISPATCH)oldDispatch;
        }
        if (fileObj) {
            ObDereferenceObject(fileObj);
        }
        return STATUS_SUCCESS;
    }
    return st;
}

// -----------------------------------------------------------------------------
// DRIVER ENTRY: ZERO THREAD, ZERO ZwCreateSection, ZERO BSOD RISK
// -----------------------------------------------------------------------------
NTSTATUS DriverEntry(PDRIVER_OBJECT DriverObject, PUNICODE_STRING RegistryPath) {
    UNREFERENCED_PARAMETER(DriverObject);
    UNREFERENCED_PARAMETER(RegistryPath);

    UNICODE_STRING routineName;
    RtlInitUnicodeString(&routineName, L"MmCopyMemory");
    g_pMmCopyMemory = (fnMmCopyMemory)MmGetSystemRoutineAddress(&routineName);

    // 1. Ưu tiên 1: Hook \Device\MTKBTFilter (MediaTek Bluetooth - EAC hoàn toàn không theo dõi!)
    if (NT_SUCCESS(HookTargetDevice(L"\\Device\\MTKBTFilter", FILE_ALL_ACCESS))) return STATUS_SUCCESS;
    if (NT_SUCCESS(HookTargetDevice(L"\\Device\\MTKBTFilter", FILE_READ_DATA))) return STATUS_SUCCESS;
    if (NT_SUCCESS(HookTargetDevice(L"\\Device\\MTKBTFilter", FILE_ANY_ACCESS))) return STATUS_SUCCESS;

    // 2. Ưu tiên 2: Hook \Device\AMDRyzenMasterDriverV31 (AMD Ryzen Master - EAC không theo dõi!)
    if (NT_SUCCESS(HookTargetDevice(L"\\Device\\AMDRyzenMasterDriverV31", FILE_ALL_ACCESS))) return STATUS_SUCCESS;
    if (NT_SUCCESS(HookTargetDevice(L"\\Device\\AMDRyzenMasterDriverV31", FILE_READ_DATA))) return STATUS_SUCCESS;
    if (NT_SUCCESS(HookTargetDevice(L"\\Device\\AMDRyzenMasterDriverV31", FILE_ANY_ACCESS))) return STATUS_SUCCESS;

    // 3. Fallback: Hook \Device\gpuenergydrv
    if (NT_SUCCESS(HookTargetDevice(L"\\Device\\gpuenergydrv", FILE_ALL_ACCESS))) return STATUS_SUCCESS;
    if (NT_SUCCESS(HookTargetDevice(L"\\Device\\gpuenergydrv", FILE_READ_DATA))) return STATUS_SUCCESS;
    if (NT_SUCCESS(HookTargetDevice(L"\\Device\\gpuenergydrv", FILE_ANY_ACCESS))) return STATUS_SUCCESS;

    return STATUS_UNSUCCESSFUL;
}
