# Changelog

Ghi theo từng phase; mới nhất ở trên.

## [1.0.1] — 2026-11-21

Bản vá sau v1.0.0: sửa 10 lỗi luật đã nêu ở mục "Lỗi đã biết" của Release v1.0.0, mỗi lỗi kèm một test hồi quy.
Người sửa: totoca6969 (khách đầu tiên, customer_left, đóng ca, khách theo kế hoạch), iamdvmk (ngưỡng ươn),
Tanh0406 (boa 0.5, kẹp uy tín, tiền cộng boa), Tanh0406 + Vũ Tuấn Đạt / datkunal làm cặp (Shop đúng giá, giữ chỗ tươi nhất).
- Quán: khách đầu tiên đến đúng `first_customer_tick`; `customer_left` mang uy tín sau thay đổi; đóng ca không trừ
  uy tín khách đang chờ; boa khi tỷ lệ kiên nhẫn đúng 0.5; kẹp uy tín khi cộng `tip_reputation`; tiền / earned cộng boa.
- Vòng ngày: khách chỉ gọi món thuộc kế hoạch Ngày; Shop cho mua khi tiền đúng bằng giá.
- Độ tươi: ươn khi `fresh < 30` (ví dụ ngưỡng của Ticket-03 phát `spoiled` ở tick 1); giữ chỗ chọn cá thể tươi nhất.

## [1.0.0] — 2026-11-21

### Phase 4 — contract v1.3, phát hành
- `contract_version: "1.3"`; thêm `bench_cmd` (`python3 -m chonoi.bench`) và `soak_cmd` (`python3 -m chonoi.soak`) ở gốc
  manifest; gameplay, tuning, kho và JSONL giữ như v1.2.
- Benchmark có render: cảnh lặn lõi, Út Sen đứng yên ở bến, Chrome / Chromium headless 1280×720, làm nóng 3 s,
  ghi `bench.json {avg_fps, p1_low_fps, frames, measured_s, load_ms}`.
- Soak: bot tất định chạy N Ngày trong một tiến trình (kế hoạch D1–D5 lặp từ Ngày 6), ghi `soak.json`.
- Cảnh báo có biểu tượng + chữ: thủy quái gần, oxy sắp hết / hết hơi, khách sắp giận; chế độ tương phản cao
  (phím H, Cài đặt ở menu chính và menu pause).
- Mở rộng: bảng xếp hạng cục bộ (`extensions: ["leaderboard"]`, `--leaderboard` + `--player-name`,
  `--export-leaderboard`); phụ đề hiệu ứng âm thanh (âm thanh WebAudio tổng hợp, M / C bật tắt).
- Sửa: event `shop_end` mang số Ngày vừa đóng (trước đây mang Ngày mới).
- Tích hợp PR #8, #9, #10; khôi phục phần sửa "số món rơi = floor(…)" bị mất khi gộp PR #9.
- Đóng gói: `LICENSE`, `CREDITS.md`, `docs/release-notes-v1.0.0.md`, `tools/package.py` (zip từ `git archive`).

### Phase 3 — contract v1.2 "Mùa Nước Nổi" (BREAKING CHANGE)
- **File kho đổi schema:** `{"items": {kind: n}}` → `{"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100}, ...]}`.
  Bên đọc v1.2 trả **mã 2** cho file kho đếm, kind lạ, id trùng, fresh ngoài [0, 100]. Kho rỗng là `{"items": []}`.
- Thêm `tuning.freshness {initial: 100, gather_decay_per_s: 0.5, quan_decay_per_s: 0.25, spoiled_below: 30}`.
- Hàng mới fresh 100, id I1, I2… theo thứ tự vào giỏ (tăng xuyên pha và Ngày); giỏ hao 0.5/s, kho quán 0.25/s
  (kể cả hàng đang giữ); fresh < 30 là ươn (event `spoiled` {item_id, kind, location}), vẫn chiếm ô, không nấu được.
- Giữ chỗ theo id (cá thể chưa ươn tươi nhất, hòa theo id); hàng giữ vừa ươn → nhả và giữ lại một lần.
- Giá món chốt lúc bắt đầu nấu: `floor(giá niêm yết × trung bình fresh / 100)`; boa tính trên giá đã chốt.
- JSONL: `hold`, `stock` (quán, Shop), `cook_started.items`, `monster_hit.lost`, `faint.lost` là mảng cá thể;
  `customers[].reserved` là mảng id.
- **Cách cập nhật fixture:**
  - `"hold": ["ca_loc", "bong_sung"]` → `"hold": [{"id": "I1", "kind": "ca_loc", "fresh": 100}, {"id": "I2", "kind": "bong_sung", "fresh": 100}]`
  - `"stock": {"ca_loc": 2}` → `"stock": [{"id": "I1", "kind": "ca_loc", "fresh": 100}, {"id": "I2", "kind": "ca_loc", "fresh": 100}]`
  - `"reserved": {"ca_loc": 1}` → `"reserved": ["I1"]` (id phải có trong kho, chưa ươn, đủ công thức)
  - Trong test Python dùng helper `items(...)`, `kinds_of(...)`, `id_kind(...)` ở `tests/helpers.py`.
- Phân tích tác động và thứ tự tích hợp: `docs/adr/0001-kho-ca-the-v12.md`.
### Phase 2 — contract v1.1
- Số chuẩn Ticket-02, 6 nguyên liệu / 6 món, 2 bếp / 4 bàn; cá bơi và sinh theo lịch; Cá Sấu Năm Chèo (M1, M2 từ Ngày 3).
- `--mode day` (D1–D5), Shop + nâng cấp oxy / Máu, pause, `--days`.
- Cửa sổ chơi: menu chính, DayIntro / EveningIntro / DayResult / Tổng kết, menu pause, Shop, HUD theo mục 2.
### Phase 1 — contract v1.0
- Gather: oxy, ngạt, Máu, ngất, dive/surface, hái nút, bắt cá, hold_full, cập bến, file kho.
- Quán: khách theo lịch, giữ chỗ, kiên nhẫn, bếp, bưng, phục vụ, boa, tiền, uy tín, quan_end.
- Kiểm fixture quán theo PRD-0 mục D (mã 2); HUD sáng/tối; hợp đồng tích hợp; skill nhóm.
