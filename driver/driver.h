#pragma once
#include <ntifs.h>
#include <ntddk.h>
#include <windef.h>

#define IOCTL_ROBRUN_READ_MEM   0x80002000
#define IOCTL_ROBRUN_WRITE_MEM  0x80002004
#define IOCTL_ROBRUN_GET_BASE   0x80002008
#define IOCTL_ROBRUN_GET_CR3    0x8000200C
#define IOCTL_ROBRUN_UNHOOK     0x80002010

#pragma pack(push, 1)

typedef struct _ROBRUN_READ_REQUEST {
    ULONG64 DirectoryTableBase;
    ULONG64 Address;
    PVOID   Response;
    SIZE_T  Size;
} ROBRUN_READ_REQUEST, *PROBRUN_READ_REQUEST;

typedef struct _ROBRUN_MODULE_REQUEST {
    ULONG   ProcessId;
    WCHAR   ModuleName[260];
    ULONG64 BaseAddress;
} ROBRUN_MODULE_REQUEST, *PROBRUN_MODULE_REQUEST;

typedef struct _ROBRUN_CR3_REQUEST {
    ULONG   ProcessId;
    ULONG64 DirectoryTableBase;
} ROBRUN_CR3_REQUEST, *PROBRUN_CR3_REQUEST;

#pragma pack(pop)

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

PPEB   PsGetProcessPeb(PEPROCESS Process);
PVOID  PsGetProcessSectionBaseAddress(PEPROCESS Process);
