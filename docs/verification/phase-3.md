# Ma trận truy vết Phase 3 (contract v1.2)

> Kết quả chạy lại trên commit `b3b72b5` (bản vá v1.0.1, toàn bộ test + script tái hiện). QA lead chạy lại trên **commit gắn tag `phase-3`** (chạy lại, không chép kết quả cũ). Bằng chứng nền: [`docs/proof/phase-3/`](../proof/phase-3/). Phân tích tác động: [`docs/adr/0001-kho-ca-the-v12.md`](../adr/0001-kho-ca-the-v12.md).

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P3-01 contract_version 1.2 + `freshness` {100, 0.5, 0.25, 30} | `test_phase2_rules::test_contract_v11_data`, xem `game.contract.json` | || Đạt (b3b72b5: 139 test OK) |
| AC-P3-02 File kho cá thể: ghi đúng một lần, sắp theo id, đủ độ chính xác, ghi nguyên tử; ngất ghi rỗng | `test_smoke_p1::Integration`, `test_phase3_freshness::Handover` | handover.txt || Đạt (b3b72b5: 139 test OK) |
| AC-P3-03 File kho đếm / sai schema / id trùng / fresh ngoài miền → mã 2 | `test_smoke_p1::test_inv_bad_schema_exit_2` | handover.txt || Đạt (b3b72b5: 139 test OK) |
| AC-P3-04 Hàng mới fresh 100, id I1… theo thứ tự vào giỏ, hao từ bước sau | `GatherFreshness` | || Đạt (b3b72b5: 139 test OK) |
| AC-P3-05 Giỏ hao 0.5/s, kho quán 0.25/s (kể cả hàng đang giữ), pause dừng hao, món chín không hao | `GatherFreshness`, `QuanFreshness` | day-handover.txt || Đạt (b3b72b5: 139 test OK) |
| AC-P3-06 Ươn khi fresh < 30; `spoiled` đúng một lần, theo id, đúng tick (ví dụ ngưỡng 30 của Ticket-03 → event ở tick 1) | `test_phase3_freshness::test_spoiled_threshold_exact_30_spoils_at_tick_1`, `test_stock_spoils_when_dropping_below_30_at_tick_61` | || Đạt (b3b72b5: 139 test OK) |
| AC-P3-07 Hàng ươn vẫn chiếm ô, không dùng nấu | `test_spoiled_once_and_still_takes_a_slot`, `test_spoiled_items_not_cookable` | || Đạt (b3b72b5: 139 test OK) |
| AC-P3-08 Giữ chỗ theo id: cá thể chưa ươn **tươi nhất**, hòa theo id | `test_phase3_freshness::test_reserve_picks_freshest_item` | || Đạt (b3b72b5: 139 test OK) |
| AC-P3-09 Hàng giữ vừa ươn: nhả + giữ lại đúng một lần; thiếu → unfulfillable | `test_reserved_item_spoils_*` | || Đạt (b3b72b5: 139 test OK) |
| AC-P3-10 Chốt giá floor(giá × TB fresh / 100), boa trên giá đã chốt; items cook_started theo kind rồi id | `test_price_locked_by_average_fresh_and_tip_on_locked_price` | || Đạt (b3b72b5: 139 test OK) |
| AC-P3-11 Bàn giao trong day: cùng tick, không hao thêm; Shop không hao; Ngày kế id mới cho giỏ mẫu | `Handover::test_day_*` | day-handover.txt || Đạt (b3b72b5: 139 test OK) |
| AC-P3-12 Scenario v1.2: hold/stock mảng cá thể, reserved mảng id; mâu thuẫn → mã 2 | `test_quan_scenario`, `test_old_count_hold_rejected` | || Đạt (b3b72b5: 139 test OK) |
| AC-P3-13 HUD đọc được độ tươi / hàng ươn | ảnh chụp 1280×720 | live-gather-freshness.png, live-quan-freshness.png || Đạt (b3b72b5: 139 test OK) |
| AC-P3-14 Regression P1–P2 còn hiệu lực đạt (test đổi có lý do trong commit) | toàn bộ test | unittest.txt || Đạt (b3b72b5: 139 test OK) |

## Đánh giá ngắn
- Yêu cầu nào đạt / chưa đạt: đạt cả 14 AC; ngưỡng ươn đúng 30 (PR #11) và giữ chỗ tươi nhất (bản vá v1.0.1) đã sửa.
- Điều cần chỉnh cho phase sau: kiểm luôn ví dụ mẫu trong ticket bằng test ngay khi đổi luật.
