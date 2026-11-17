#pragma once
#include <ntifs.h>
#include <ntddk.h>
#include <windef.h>

// ============================================================================
// SHARED MEMORY RENDEZVOUS PROTOCOL
// Zero IOCTL hook. Zero unbacked dispatch pointers. Zero EAC E-0503.
//
// Architecture:
//   Kernel thread polls g_ShmKernel->RequestReady (spin + KeDelayExecutionThread).
//   User maps \BaseNamedObjects\RobRunShm, writes req, sets flag, waits on resp.
//   Kernel processes, writes resp, clears flag.
//
// EAC stealth: no MajorFunction[] ever touched on any registered DriverObject.
//   Every code pointer in the kernel lives inside RobRunMem.sys .text section.
// ============================================================================

// Shared memory object name (kernel-visible path)
#define ROBRUN_SHM_NAME      L"\\BaseNamedObjects\\RobRunShm"
// Size of the shared ring (must be page-aligned, >= sizeof(ROBRUN_SHM))
#define ROBRUN_SHM_SIZE      0x2000  // 8 KB

// Op-codes  (ShmHeader.OpCode)
#define OP_NOP               0x00
#define OP_READ_MEM          0x01
#define OP_GET_BASE          0x02
#define OP_GET_CR3           0x03
#define OP_PING              0x04
#define OP_SHUTDOWN          0xFF

// Status codes (ShmHeader.Status — written by kernel after processing)
#define RSTAT_OK             0x00
#define RSTAT_ERR            0x01
#define RSTAT_BUSY           0x02
#define RSTAT_INVALID        0x03

// ----------------------------------------------------------------------------
// Shared memory layout (fits in ROBRUN_SHM_SIZE)
// ----------------------------------------------------------------------------
#pragma pack(push, 1)

typedef struct _ROBRUN_SHM_HEADER {
    // REQUEST side (written by user, cleared by kernel)
    volatile ULONG  RequestReady;    // 0 = idle, 1 = pending, 0xDEAD = shutdown
    ULONG           OpCode;
    ULONG           ProcessId;
    ULONG           Pad0;
    ULONG64         DirectoryTableBase;
    ULONG64         Address;
    ULONG64         Size;
    WCHAR           ModuleName[260]; // for OP_GET_BASE

    // RESPONSE side (written by kernel, read by user)
    volatile ULONG  ResponseReady;   // 0 = not ready, 1 = done
    ULONG           Status;          // RSTAT_*
    ULONG64         ResultBase;      // base address / CR3 / bytes read
    ULONG64         ResultCr3;
} ROBRUN_SHM_HEADER, *PROBRUN_SHM_HEADER;

// Data payload immediately follows the header in the shared mapping.
// Kernel writes read data here; user reads it.
// Max read size = ROBRUN_SHM_SIZE - sizeof(ROBRUN_SHM_HEADER)
#define ROBRUN_SHM_DATA_OFFSET  sizeof(ROBRUN_SHM_HEADER)
#define ROBRUN_SHM_MAX_READ     (ROBRUN_SHM_SIZE - ROBRUN_SHM_DATA_OFFSET)

#pragma pack(pop)

// ----------------------------------------------------------------------------
// Physical memory helpers (unchanged — pure CR3 walk, zero ETW-TI)
// ----------------------------------------------------------------------------
#define MM_COPY_MEMORY_PHYSICAL  0x1
#define MM_COPY_MEMORY_VIRTUAL   0x2

typedef union _MM_COPY_ADDRESS {
    PVOID            VirtualAddress;
    PHYSICAL_ADDRESS PhysicalAddress;
} MM_COPY_ADDRESS, *PMM_COPY_ADDRESS;

typedef NTSTATUS (NTAPI *fnMmCopyMemory)(
    PVOID             TargetAddress,
    MM_COPY_ADDRESS   SourceAddress,
    SIZE_T            NumberOfBytes,
    ULONG             Flags,
    PSIZE_T           NumberOfBytesTransferred
);

// Kernel exports we depend on
PPEB   PsGetProcessPeb(PEPROCESS Process);
PVOID  PsGetProcessSectionBaseAddress(PEPROCESS Process);
