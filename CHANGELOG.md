# Changelog
## Unreleased
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
### Phase 2 (contract v1.1)
- Số chuẩn Ticket-02, 6 nguyên liệu / 6 món, 2 bếp / 4 bàn; cá bơi và sinh theo lịch; Cá Sấu Năm Chèo (M1, M2 từ Ngày 3).
- `--mode day` (D1–D5), Shop + nâng cấp oxy / Máu, pause, `--days`.
- Cửa sổ chơi: menu chính, DayIntro / EveningIntro / DayResult / Tổng kết, menu pause, Shop, HUD theo mục 2.
### Phase 1
- Gather: oxy, ngạt, Máu, ngất, dive/surface, hái nút, bắt cá, hold_full, cập bến, file kho.
- Quán: khách theo lịch, giữ chỗ, kiên nhẫn, bếp, bưng, phục vụ, boa, tiền, uy tín, quan_end.
- Kiểm fixture quán theo PRD-0 mục D (mã 2); HUD sáng/tối; hợp đồng tích hợp; skill nhóm.
