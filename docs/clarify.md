# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 2026-11-21 P1 | Khách fixture ở đơn `reserved` thiếu `reserved` mà kho không đủ thì sao? | Giả định: đơn chuyển `unfulfillable`, giữ chỗ rỗng (không báo mã 2 vì PRD nói "cấp theo công thức"). | Integrator |
| 2 | 2026-11-21 P1 | Bếp idle có cần tay trống mới nấu được không? | Giả định: không cần; chỉ bưng món mới cần tay trống (`carry_limit` = 1). | Integrator |
| 3 | 2026-11-21 P1 | Trước khi nấu, `base_price` / `tip` của khách là gì? | Giả định: `null`; `base_price` chốt ở `cook_started`, `tip` chốt ở `served`. | Integrator |
| 4 | 2026-11-21 P1 | Id khách tự sinh dùng tiền tố nào? | Giả định: `C` (C1, C2, …), nối sau hậu tố lớn nhất của khách fixture. | Integrator |
| 5 | 2026-11-21 P1 | Uy tín là số thực, `floor` có lệch do sai số (3.9999…)? | Làm tròn uy tín 9 chữ số sau mỗi lần cộng/trừ rồi mới kẹp và `floor`. | Integrator |
| 6 | 2026-11-21 P2 | 8 đàn đầu ca chọn thế nào? | Dùng đúng thủ tục sinh theo lịch (trọng số loài, điểm cách > 1 m) lặp 8 lần, không phát `fish_spawned`. | Integrator |
| 7 | 2026-11-21 P2 | "Đổi hướng theo seed" là góc gì? | Góc đều trong [0°, 360°) từ luồng RNG `fish_turn`; hướng ban đầu cá mới từ luồng `fish_spawn`. | Integrator |
| 8 | 2026-11-21 P2 | Id cá / khách qua nhiều Ngày? | Một `IdAllocator` cho cả lượt: id nối tiếp, không cấp lại trong lượt (F9… ở Ngày 2). | Integrator |
| 9 | 2026-11-21 P2 | `recoil_dist` là tổng hay mỗi bước? | Tổng 2 m chia đều 60 bước (2/60 m/bước) như đề ghi. | Integrator |
| 10 | 2026-11-21 P2 | Lệnh `buy` là `weapon`/`net` khi chưa làm mở rộng? | `buy_failed` reason `unknown` (đề: "Shop phát buy_failed nếu gặp lệnh không hỗ trợ"). | Integrator |
| 11 | 2026-11-21 P2 | DayIntro / EveningIntro / DayResult có phải pha headless? | Không; chỉ là màn của cửa sổ chơi, sim dừng bước trong lúc hiện màn (headless không đổi). | Integrator |
