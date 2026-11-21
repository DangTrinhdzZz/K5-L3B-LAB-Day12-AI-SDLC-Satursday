# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 2026-11-21 P1 | Khách fixture ở đơn `reserved` thiếu `reserved` mà kho không đủ thì sao? | Giả định: đơn chuyển `unfulfillable`, giữ chỗ rỗng (không báo mã 2 vì PRD nói "cấp theo công thức"). | Integrator |
| 2 | 2026-11-21 P1 | Bếp idle có cần tay trống mới nấu được không? | Giả định: không cần; chỉ bưng món mới cần tay trống (`carry_limit` = 1). | Integrator |
| 3 | 2026-11-21 P1 | Trước khi nấu, `base_price` / `tip` của khách là gì? | Giả định: `null`; `base_price` chốt ở `cook_started`, `tip` chốt ở `served`. | Integrator |
| 4 | 2026-11-21 P1 | Id khách tự sinh dùng tiền tố nào? | Giả định: `C` (C1, C2, …), nối sau hậu tố lớn nhất của khách fixture. | Integrator |
| 5 | 2026-11-21 P1 | Uy tín là số thực, `floor` có lệch do sai số (3.9999…)? | Làm tròn uy tín 9 chữ số sau mỗi lần cộng/trừ rồi mới kẹp và `floor`. | Integrator |
