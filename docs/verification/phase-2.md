# Ma trận truy vết Phase 2

> QA lead điền cột "Kết quả" trên **commit gắn tag `phase-2`** (chạy lại, không chép kết quả cũ). Bằng chứng nền: [`docs/proof/phase-2/`](../proof/phase-2/).

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P2-01 contract v1.1, số chuẩn, 6 nguyên liệu / 6 món | `tests/test_phase2_rules.py::StandardNumbers` | unittest.txt | |
| AC-P2-02 Cá bơi 1.5 m/s, đổi hướng bước 120k, phản xạ mép (cả mép x và d) | `FishSwim` | | |
| AC-P2-03 8 đàn đầu ca, sinh theo lịch 360k, trần 12, `random_fish:false` | `FishSwim` | | |
| AC-P2-04 Cá Sấu patrol / chase (ngưỡng d ≥ 10, ≤ 10 m) / thoát chase | `Crocodile` | | |
| AC-P2-05 Hit: −1 Máu, rơi `floor(n/2)` LIFO, bất tử 90, recoil 60 | `Crocodile` | | |
| AC-P2-06 Ngất do quái / ngạt vẫn mở quán với kho rỗng | `test_day_mode::test_faint_still_opens_quan_with_empty_stock` | | |
| AC-P2-07 2 bếp / 4 bàn, món mới nấu được | `QuanV11` | integration.txt | |
| AC-P2-08 Trong day, khách chỉ gọi món thuộc kế hoạch Ngày | (cần test) | | |
| AC-P2-09 `--mode day` công bố đúng kế hoạch D1–D5, thứ tự đổi pha | `DayFlow` | day-1.txt | |
| AC-P2-10 Shop: mua khi đủ (kể cả đúng giá), trừ money giữ earned, buy_failed, đóng done/time | `DayFlow` | day-upgrade.txt | |
| AC-P2-11 Cấp mua áp từ Ngày kế (hp_max, oxygen_max) | `test_buy_hp_applies_next_day` | day-upgrade.txt | |
| AC-P2-12 Pause: paused/resumed, timer đứng yên, resume chạy gameplay ngay bước đó | `Pause` | | |
| AC-P2-13 Menu, intro, pause menu, HUD sáng/tối, chữ ≥ 18 px ở 1280×720 | ảnh chụp | live-*.png | |
| AC-P2-14 Một Ngày headless ≤ 20 s | `test_one_full_day_phases_and_end` | day-1.txt | |
| AC-P2-15 Smoke tích hợp gather → kho → quan (phút 20) | skill `smoke-hai-tien-trinh` | integration.txt | |
| AC-P2-16 Regression P1 với số chuẩn (test cũ đổi có lý do trong commit) | toàn bộ test | unittest.txt | |

## Đánh giá ngắn
- Yêu cầu nào đạt / chưa đạt:
- Điều cần chỉnh cho phase sau:
