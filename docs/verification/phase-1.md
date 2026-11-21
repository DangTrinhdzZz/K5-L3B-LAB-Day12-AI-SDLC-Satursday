# Ma trận truy vết Phase 1

> QA lead điền cột "Kết quả" trên **commit gắn tag `phase-1`** (chạy lại, không chép kết quả cũ). Bằng chứng nền: [`docs/proof/phase-1/`](../proof/phase-1/).

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P1-01 Oxy trừ dưới nước / hồi ở mặt nước, kẹp [0, max] | `tests/test_gather_rules.py::Oxygen` | unittest.txt | |
| AC-P1-02 `oxygen_empty`, ngạt đúng tick (t+59), `choke` hp sau trừ | test lát 1 | | |
| AC-P1-03 Ngất: `faint.lost` LIFO, `gather_end` fainted, kho rỗng | test lát 1 | | |
| AC-P1-04 `dive` / `surface` đúng biên d ≤ 0.5 | test lát 1 | | |
| AC-P1-05 Hái nút ready gần nhất (tính cả đúng mép), chỉ ở mặt nước | `Harvest` | | |
| AC-P1-06 Mọc lại sau `regrow_s × 60` tick, `node_regrown` | test lát 2 | | |
| AC-P1-07 Bắt cá: đúng đàn gần nhất, yield, cooldown; `hold_full` không đặt cooldown, không thử đàn khác | `Catch` | | |
| AC-P1-08 Cập bến xét trước hái; kho ghi đúng một lần | `DockInventory`, smoke | smoke-hai-tien-trinh.txt | |
| AC-P1-09 Khách đến tick 120 rồi mỗi 15 s, bàn trống id nhỏ nhất | `Customers` | | |
| AC-P1-10 Giữ chỗ theo công thức, `no_dish` | `Customers` | | |
| AC-P1-11 Hết kiên nhẫn: `customer_left` + uy tín −0.5 (event mang uy tín sau đổi) | `Customers` | | |
| AC-P1-12 Nấu / chín / bưng (`cook_started` items, `dish_ready`, `dish_picked`) | `Kitchen` | | |
| AC-P1-13 Phục vụ + boa (tỷ lệ ≥ 0.5), `paid.amount` = giá + boa, tiền cộng cả boa | `Serve` | | |
| AC-P1-14 Uy tín kẹp [0, 5]; đóng ca không trừ uy tín | `Shift` | | |
| AC-P1-15 `quan_end`, dòng `end`, `score = earned + 100 × floor(rep)` | `Shift` | | |
| AC-P1-16 Fixture mâu thuẫn → mã 2 trước khi ghi đầu ra | `tests/test_quan_scenario.py` | | |
| AC-P1-17 HUD sáng/tối đọc được | chơi thử `python3 -m chonoi.live` (ảnh chụp) | | |
| AC-P1-18 Smoke hai tiến trình: quán nhận đúng kho | skill `smoke-hai-tien-trinh` | smoke-hai-tien-trinh.txt | |

## Đánh giá ngắn
- Yêu cầu nào đạt / chưa đạt:
- Điều cần chỉnh cho phase sau:
