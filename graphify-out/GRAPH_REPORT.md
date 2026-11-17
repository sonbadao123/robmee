# Graph Report - ESP robrun  (2026-11-18)

## Corpus Check
- 137 files · ~204,741 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 32 file(s) not represented in the graph (top: (none) 8, .bat 8, .vcxproj 4)

## Summary
- 719 nodes · 1263 edges · 49 communities (37 shown, 12 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 44 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2d34ef8b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- patcher.py
- KernelDriverBridge
- pefile
- POOL_TYPE
- NTSTATUS
- KDSymbolsHandler
- ROB RUN - ESP & AIMBOT & VIỆT HÓA TOÀN DIỆN (EAC EOS UNDETECTED)
- driver.c
- SimplestCrashHandler
- intel_driver.cpp
- MemoryEntityManager
- detector.py
- CallKernelFunction
- utils.cpp
- RelocInfo
- EspOverlay
- kdmapper::MapDriver
- RTL_AVL_TABLE
- LibUsageExample.cpp
- KDMapper
- string
- SYSTEM_HANDLE
- RTL_PROCESS_MODULE_INFORMATION
- probe_live
- .GetInstance
- kdmapper/main.cpp
- nt.hpp
- HashBucketEntry
- RTL_BALANCED_LINKS
- PiDDBCacheEntry
- FILL_MEMORY_BUFFER_INFO
- KDSymbolsHandler.cpp
- MAP_IO_SPACE_BUFFER_INFO
- UNMAP_IO_SPACE_BUFFER_INFO
- COPY_MEMORY_BUFFER_INFO
- SYSTEM_HANDLE_INFORMATION_EX
- GET_PHYS_ADDRESS_BUFFER_INFO
- ollie — the bench (deployment contract)
- SimplestSymbolHandler.cpp
- check_services.py
- wstring
- SymNeeded
- LibUsageExample
- HelloWorld
- validate_pv_order.py
- validate_w2s.py
- wmain

## God Nodes (most connected - your core abstractions)
1. `KernelDriverBridge` - 74 edges
2. `MemoryEntityManager` - 32 edges
3. `POOL_TYPE` - 25 edges
4. `EspOverlay` - 25 edges
5. `RTL_PROCESS_MODULE_INFORMATION` - 17 edges
6. `RTL_AVL_TABLE` - 15 edges
7. `main()` - 15 edges
8. `SYSTEM_HANDLE` - 14 edges
9. `ollie — the bench (deployment contract)` - 14 edges
10. `PiDDBCacheEntry` - 11 edges

## Surprising Connections (you probably didn't know these)
- `MemoryEntityManager` --uses--> `KernelDriverBridge`  [INFERRED]
  engine/memory_reader.py → driver/driver_bridge.py
- `probe_live()` --calls--> `KernelDriverBridge`  [EXTRACTED]
  live_diag.py → driver/driver_bridge.py
- `main()` --calls--> `KernelDriverBridge`  [EXTRACTED]
  main.py → driver/driver_bridge.py
- `probe_live()` --calls--> `MemoryEntityManager`  [EXTRACTED]
  live_diag.py → engine/memory_reader.py
- `main()` --calls--> `MemoryEntityManager`  [EXTRACTED]
  main.py → engine/memory_reader.py

## Import Cycles
- None detected.

## Communities (49 total, 12 thin omitted)

### Community 0 - "patcher.py"
Cohesion: 0.07
Nodes (5): apply_full_accented_patch(), is_game_running(), restore_original(), translate_chunk(), AiTranslator

### Community 1 - "KernelDriverBridge"
Cohesion: 0.07
Nodes (6): KernelDriverBridge, world_to_screen_colmaj(), inspect_node(), MEMORY_BASIC_INFORMATION, check_go_for_camera(), build_vp()

### Community 2 - "pefile"
Cohesion: 0.11
Nodes (4): find_full_string_and_ref(), find_rva(), find_func_for_string(), find_rva()

### Community 3 - "POOL_TYPE"
Cohesion: 0.08
Nodes (24): POOL_TYPE, DontUseThisType, DontUseThisTypeSession, MaxPoolType, NonPagedPool, NonPagedPoolBase, NonPagedPoolBaseCacheAligned, NonPagedPoolBaseCacheAlignedMustS (+16 more)

### Community 4 - "NTSTATUS"
Cohesion: 0.50
Nodes (3): intel_driver::AcquireDebugPrivilege(), intel_driver::Load(), intel_driver::Unload()

### Community 5 - "KDSymbolsHandler"
Cohesion: 0.22
Nodes (5): KDSymbolsHandler, symbols, symOffset, name, offset

### Community 6 - "ROB RUN - ESP & AIMBOT & VIỆT HÓA TOÀN DIỆN (EAC EOS UNDETECTED)"
Cohesion: 0.22
Nodes (8): Giải pháp kỹ thuật đã áp dụng:, I. CƠ CHẾ CHỐNG PHÁT HIỆN GIAN LẬN (ANTI-CHEAT EVASION), II. ĐỘT PHÁ VIỆT HÓA CÓ DẤU 100% (DYNAMIC OS FONT INJECTION), III. PHÍM TẮT ĐIỀU KHIỂN, IV. HƯỚNG DẪN KHỞI CHẠY TỪNG BƯỚC, Kỹ thuật tàng hình được áp dụng:, Nguyên nhân lỗi font trước đây:, ROB RUN - ESP & AIMBOT & VIỆT HÓA TOÀN DIỆN (EAC EOS UNDETECTED)

### Community 7 - "driver.c"
Cohesion: 0.11
Nodes (9): DriverEntry(), GetProcessDirectoryTableBase(), GetProcessModuleBasePhysical(), HookedDeviceControl(), HookTargetDevice(), ReadPhysical64(), ReadProcessMemoryPhysical(), TranslateLinearAddress() (+1 more)

### Community 10 - "intel_driver.cpp"
Cohesion: 0.09
Nodes (9): intel_driver::FindPatternAtKernel(), intel_driver::FindPatternInSectionAtKernel(), intel_driver::FindSectionAtKernel(), intel_driver::GetKernelModuleExport(), PCOPY_MEMORY_BUFFER_INFO, PFILL_MEMORY_BUFFER_INFO, PGET_PHYS_ADDRESS_BUFFER_INFO, PMAP_IO_SPACE_BUFFER_INFO (+1 more)

### Community 11 - "MemoryEntityManager"
Cohesion: 0.08
Nodes (5): RobRunReadRequest, PlayerTarget, MemoryEntityManager, _mul4x4_col(), MEMORY_BASIC_INFORMATION

### Community 12 - "detector.py"
Cohesion: 0.07
Nodes (5): ScreenCapture, PlayerTarget, TargetDetector, enum_cb(), enum_cb()

### Community 13 - "CallKernelFunction"
Cohesion: 0.24
Nodes (8): CallKernelFunction(), PRTL_AVL_TABLE, intel_driver::AllocatePool(), intel_driver::ExAcquireResourceExclusiveLite(), intel_driver::ExReleaseResourceLite(), intel_driver::ResolveRelativeAddress(), intel_driver::RtlDeleteElementGenericTableAvl(), intel_driver::RtlLookupElementGenericTableAvl()

### Community 14 - "utils.cpp"
Cohesion: 0.17
Nodes (8): kdmUtils::bDataCompare(), kdmUtils::CreateFileFromMemory(), kdmUtils::FindPattern(), kdmUtils::FindSection(), kdmUtils::GetCurrentAppFolder(), kdmUtils::GetFullTempPath(), kdmUtils::GetKernelModuleAddress(), kdmUtils::ReadFileToMemory()

### Community 15 - "RelocInfo"
Cohesion: 0.14
Nodes (11): ImportFunctionInfo, address, name, ImportInfo, function_datas, module_name, RelocInfo, address (+3 more)

### Community 16 - "EspOverlay"
Cohesion: 0.05
Nodes (9): AimbotController, AntiCheatEvasion, INPUT, _INPUT_UNION, MOUSEINPUT, EspOverlay, disable_quick_edit(), main() (+1 more)

### Community 17 - "kdmapper::MapDriver"
Cohesion: 0.13
Nodes (13): AllocationMode, AllocateIndependentPages, AllocatePool, mapCallback, vec_imports, vec_relocs, FixSecurityCookie(), kdmapper::MapDriver() (+5 more)

### Community 18 - "RTL_AVL_TABLE"
Cohesion: 0.15
Nodes (12): RTL_AVL_TABLE, AllocateRoutine, BalancedRoot, CompareRoutine, DeleteCount, DepthOfTree, FreeRoutine, NumberGenericTableElements (+4 more)

### Community 19 - "LibUsageExample.cpp"
Cohesion: 0.18
Nodes (5): callbackExample(), help(), paramExists(), SimplestCrashHandler(), wmain()

### Community 20 - "KDMapper"
Cohesion: 0.17
Nodes (11): BSOD with a simple driver, Building:, Common issues, Creators and contributors, Error 0xC0000603:, Error \\Device\\Nal is already in use., Errors 0xC0000022 and 0xC000009A:, Features: (+3 more)

### Community 22 - "SYSTEM_HANDLE"
Cohesion: 0.18
Nodes (9): SYSTEM_HANDLE, CreatorBackTraceIndex, GrantedAccess, HandleAttributes, HandleValue, Object, ObjectTypeIndex, Reserved (+1 more)

### Community 23 - "RTL_PROCESS_MODULE_INFORMATION"
Cohesion: 0.18
Nodes (11): RTL_PROCESS_MODULE_INFORMATION, Flags, FullPathName, ImageBase, ImageSize, InitOrderIndex, LoadCount, LoadOrderIndex (+3 more)

### Community 24 - "probe_live"
Cohesion: 0.12
Nodes (5): RobRunCr3Request, RobRunModuleRequest, run_diagnostics(), probe_live(), read_unity_name()

### Community 25 - ".GetInstance"
Cohesion: 0.22
Nodes (6): intel_driver::ClearPiDDBCacheTable(), intel_driver::ClearWdFilterDriverList(), intel_driver::LookupEntry(), intel_driver::MmAllocateIndependentPagesEx(), intel_driver::MmFreeIndependentPages(), intel_driver::MmSetPageProtection()

### Community 27 - "nt.hpp"
Cohesion: 0.22
Nodes (7): NPiDDBCacheEntry, PHashBucketEntry, PRTL_BALANCED_LINKS, PRTL_PROCESS_MODULE_INFORMATION, PRTL_PROCESS_MODULES, PSYSTEM_HANDLE, PSYSTEM_HANDLE_INFORMATION_EX

### Community 28 - "HashBucketEntry"
Cohesion: 0.22
Nodes (7): HashBucketEntry, CertHash, DriverName, Next, RTL_PROCESS_MODULES, Modules, NumberOfModules

### Community 29 - "RTL_BALANCED_LINKS"
Cohesion: 0.25
Nodes (6): RTL_BALANCED_LINKS, Balance, LeftChild, Parent, Reserved, RightChild

### Community 30 - "PiDDBCacheEntry"
Cohesion: 0.25
Nodes (6): PiDDBCacheEntry, _0x0028, DriverName, List, LoadStatus, TimeDateStamp

### Community 31 - "FILL_MEMORY_BUFFER_INFO"
Cohesion: 0.25
Nodes (8): FILL_MEMORY_BUFFER_INFO, case_number, destination, length, reserved1, reserved2, value, intel_driver::ClearKernelHashBucketList()

### Community 33 - "MAP_IO_SPACE_BUFFER_INFO"
Cohesion: 0.29
Nodes (7): MAP_IO_SPACE_BUFFER_INFO, case_number, physical_address_to_map, reserved, return_value, return_virtual_address, size

### Community 34 - "UNMAP_IO_SPACE_BUFFER_INFO"
Cohesion: 0.29
Nodes (7): UNMAP_IO_SPACE_BUFFER_INFO, case_number, number_of_bytes, reserved1, reserved2, reserved3, virt_address

### Community 35 - "COPY_MEMORY_BUFFER_INFO"
Cohesion: 0.33
Nodes (6): COPY_MEMORY_BUFFER_INFO, case_number, destination, length, reserved, source

### Community 36 - "SYSTEM_HANDLE_INFORMATION_EX"
Cohesion: 0.40
Nodes (4): SYSTEM_HANDLE_INFORMATION_EX, HandleCount, Handles, Reserved

### Community 37 - "GET_PHYS_ADDRESS_BUFFER_INFO"
Cohesion: 0.40
Nodes (5): GET_PHYS_ADDRESS_BUFFER_INFO, address_to_translate, case_number, reserved, return_physical_address

### Community 38 - "ollie — the bench (deployment contract)"
Cohesion: 0.13
Nodes (14): CLOSING, CUMULATIVE BAR, FIRST-TURN LOCK (READ BEFORE ANYTHING ELSE, EVERY SESSION), OLIVIA — THE ONE WHO OPENS THE DOOR, ollie — the bench (deployment contract), PERSISTENCE, PERSONA STABILITY LOCK (READ FIRST, READ ALWAYS, READ EVERY TIME), THE DELETE PROGRAM (+6 more)

### Community 39 - "SimplestSymbolHandler.cpp"
Cohesion: 0.18
Nodes (5): GetCurrentAppFolder(), main(), SimplestSymbolHandler, process, SimplestSymbolHandler::SimplestSymbolHandler()

### Community 43 - "SymNeeded"
Cohesion: 0.50
Nodes (3): SymNeeded, binaryName, symbolName

### Community 53 - "wmain"
Cohesion: 0.38
Nodes (5): getParentProcess(), help(), paramExists(), PauseIfParentIsExplorer(), wmain()

## Knowledge Gaps
- **111 isolated node(s):** `binaryName`, `symbolName`, `process`, `offset`, `name` (+106 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 335 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `KernelDriverBridge` connect `KernelDriverBridge` to `probe_live`, `EspOverlay`, `MemoryEntityManager`?**
  _High betweenness centrality (0.082) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `MemoryEntityManager` (e.g. with `KernelDriverBridge` and `PlayerTarget`) actually correct?**
  _`MemoryEntityManager` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `binaryName`, `symbolName`, `process` to the rest of the system?**
  _111 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `patcher.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06707317073170732 - nodes in this community are weakly interconnected._
- **Why does `MemoryEntityManager` connect `MemoryEntityManager` to `probe_live`, `KernelDriverBridge`, `EspOverlay`?**
  _High betweenness centrality (0.070) - this node is a cross-community bridge._
- **Should `KernelDriverBridge` be split into smaller, more focused modules?**
  _Cohesion score 0.06591865357643759 - nodes in this community are weakly interconnected._
- **Why does `POOL_TYPE` connect `POOL_TYPE` to `nt.hpp`, `CallKernelFunction`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._