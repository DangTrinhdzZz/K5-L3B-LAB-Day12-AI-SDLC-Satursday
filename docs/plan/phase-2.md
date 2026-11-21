# Kế hoạch Phase 2 (re-planning 5 phút)

- **Mục tiêu:** số chuẩn + contract v1.1; cá bơi/sinh; Cá Sấu, Máu/ngất; 2 bếp / 4 bàn / 6 món; `--mode day` D1–D5 với Shop và nâng cấp; pause, menu, HUD; tag `phase-2` trước 1:55.
- **So với giả định Phase 1:** số liệu cũ giữ nguyên (đã đúng preset); đổi: `fish_initial` là số đàn, thêm nguyên liệu / món / bếp / bàn; 4 test cũ phải cập nhật (ghi lý do trong commit).
- **Giao diện chuyển pha (chốt):** `DaySim` giữ money/earned/uy tín/cấp, dựng `GatherSim` → `QuanSim` → `ShopSim`; sim trả `(name, data, phase)`; `Session` lo pause và ba bộ đếm tick.

| Lát | Việc | AC | Người |
|---|---|---|---|
| 1 | Số chuẩn, cá bơi / sinh | AC-P2-01..03 | Tanh0406 → rà/sửa: Người 1 |
| 2 | Cá Sấu, Máu, ngất | AC-P2-04..06 | Tanh0406 → rà/sửa: Người 2, 3 |
| 3 | 2 bếp / 4 bàn, 6 món, kế hoạch ngày | AC-P2-07..08 | Tanh0406 → rà/sửa: Người 4 |
| 4 | day, Shop, pause, menu, HUD | AC-P2-09..14 | Tanh0406 → rà/sửa: Người 5, 6 |
| QA | Smoke tích hợp phút 20, smoke day, regression P1 | AC-P2-15..16 | QA lead |

- **Rủi ro:** nhiều người cùng sửa `gather.py` (lỗi P1 + P2) → `git pull --rebase` trước mỗi commit; luật cá/quái nhiều chi tiết biên → mỗi sửa kèm test hồi quy.
