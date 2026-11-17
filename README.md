# ROB RUN - ESP & AIMBOT & VIỆT HÓA TOÀN DIỆN (EAC EOS UNDETECTED)

Dự án chuyên dụng cho game **ROB RUN** (Unity IL2CPP 64-bit, Easy Anti-Cheat EOS) bao gồm:
1. **Bộ ESP & Aimbot tàng hình:** Tự ngắm mượt, không aim đồng đội, chỉ ngắm Cướp và Cảnh sát, vượt mặt hệ thống chống gian lận EAC EOS.
2. **Bộ Việt Hóa ĐỘT PHÁ CÓ DẤU 100% (Dynamic OS Font Injection):** Mở khóa cơ chế nạp ký tự động của TextMeshPro qua font hệ thống Windows (`arial.ttf`), loại bỏ 100% tình trạng rụng dấu/khoảng trắng, giữ nguyên tiếng Việt có dấu chuẩn đẹp.

---

## I. CƠ CHẾ CHỐNG PHÁT HIỆN GIAN LẬN (ANTI-CHEAT EVASION)

Game được bảo vệ bởi **Easy Anti-Cheat EOS** (`start_protected_game.exe` + driver `EasyAntiCheat_EOS.sys`). Driver kernel của EAC tước cờ `PROCESS_VM_READ` (0x0010) và chặn mọi handle can thiệp bộ nhớ từ bên ngoài.

### Kỹ thuật tàng hình được áp dụng:
1. **Zero-Memory Attachment (Không chạm bộ nhớ game):**
   - Hoạt động 100% thông qua thị giác máy tính ngoài (External Computer Vision), phân tích khung hình từ viewport màn hình.
   - Không gọi `OpenProcess`, không gọi `ReadProcessMemory`, không dùng DLL injection -> EAC hoàn toàn mù đối với tiến trình này.
2. **Quỹ đạo chuột Bezier bậc 3 (Cubic Bezier Curves):**
   - Thuật toán mô phỏng đường cong gia tốc tay người thật, loại bỏ hoàn toàn các cú snap thẳng tắp phi tự nhiên nhằm vượt qua bộ lọc phân tích hành vi chuột (Heuristic Mouse Analytics).
   - Thêm vi dao động ngẫu nhiên 1-pixel (Micro-Jitter) và độ trễ ngẫu nhiên 2-5ms giữa các gói tin chuột.
3. **Overlay Xuyên Thấu (Click-Through Overlay):**
   - Cửa sổ trong suốt chuẩn Win32 Layered (`WS_EX_TRANSPARENT | WS_EX_LAYERED`), vẽ đè trực tiếp lên game mà không bao giờ chiếm focus chuột hay cản trở thao tác bắn súng.

---

## II. ĐỘT PHÁ VIỆT HÓA CÓ DẤU 100% (DYNAMIC OS FONT INJECTION)

### Nguyên nhân lỗi font trước đây:
Game gốc sử dụng bộ font nướng tĩnh (Static Texture Atlas) chỉ có 276 ký tự (tiếng Anh và tiếng Nga). Toàn bộ ký tự có dấu của tiếng Việt (`ò, ệ, ớ, ữ, ườ, ể, ộ, ự, ủ, ỗ, ả, đ...`) đều không có trong texture atlas, khiến TextMeshPro tự động đục lỗ thành khoảng trắng (`L I`, `ã x y ra l i`...).

### Giải pháp kỹ thuật đã áp dụng:
1. **Can thiệp Font Asset (`inbuild_assets_all.bundle`):**
   - Chuyển chế độ nạp texture `m_AtlasPopulationMode` từ 0 (Static) sang **1 (Dynamic)**.
   - Bật cờ `InternalDynamicOS = 1` và `m_IsMultiAtlasTexturesEnabled = 1`.
   - Trỏ đường dẫn font gốc sang font hệ thống Windows: `C:\Windows\Fonts\arial.ttf`.
   - Khi TextMeshPro gặp bất kỳ ký tự có dấu nào của Tiếng Việt, nó sẽ tự động vẽ thêm ký tự đó vào Texture Atlas thời gian thực!
2. **Nạp 4.822 chuỗi Tiếng Việt CÓ DẤU chuẩn xác:**
   - Đầy đủ ngữ cảnh gaming: Trả nợ cho Lenny, Nhà nghỉ của Lenny, Hàng vận chuyển, Tủ chìa khóa, Cốp xe, Két sắt, Nhận hối lộ, Tống giam, Áo giáp chống đạn...

---

## III. PHÍM TẮT ĐIỀU KHIỂN

| Phím | Chức năng | Âm thanh xác nhận |
| :--- | :--- | :--- |
| **Giữ Chuột Phải** (`Right Click`) | **Tự động ngắm (Aimbot)** | Bám tâm mượt vào Cướp hoặc Cảnh sát trong vòng FOV |
| **F1** | **Bật / Tắt ESP** | Bíp cao (Bật) / Bíp trầm (Tắt) |
| **F2** | **Bật / Tắt Tự ngắm** | Bíp cao (Bật) / Bíp trầm (Tắt) |
| **F3** | **Bật / Tắt Vòng FOV** | Bíp nhẹ xác nhận |
| **F12** | **Nút Khẩn Cấp (Panic Key)** | Bíp dài trầm và tắt ngay lập tức |

---

## IV. HƯỚNG DẪN KHỞI CHẠY TỪNG BƯỚC

1. Trong game **ROB RUN**, vào **Cài đặt (Settings) -> Đồ họa (Graphics) -> Chuyển sang "Không viền" (Borderless)**.
2. Bật `start.bat` để chạy ESP & Aimbot.
3. Vào trận và chiến đấu!
