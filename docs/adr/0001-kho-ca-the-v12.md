# ADR-0001: Kho cá thể có độ tươi (Change Request "Mùa Nước Nổi", contract v1.2)

- Trạng thái: chấp nhận
- Ngày, người quyết: 2026-11-21, Integrator (Tanh0406), thông qua ở 7 phút đầu Phase 3

## Bối cảnh
Ticket-03 thay kho đếm `{"items": {kind: n}}` bằng kho cá thể `{"items": [{id, kind, fresh}]}`. Giữ chỗ chuyển từ
theo lượng sang theo id, giá món chốt theo độ tươi, có sự kiện `spoiled`. Đây là breaking change ở hợp đồng giữa
Lặn và Quán (file kho và bàn giao trong day), ảnh hưởng mọi lát.

## Các lựa chọn đã cân nhắc
1. **Hỗ trợ song song v1.1 và v1.2** (đọc cả hai schema, chọn theo `contract_version`). An toàn khi tích hợp từng
   phần, nhưng thêm nhánh code và test cho schema sẽ bị bỏ ngay trong phase.
2. **Chuyển hẳn sang v1.2 trong một commit tích hợp**: adapter (`inventory.py`, `freshness.py`), Lặn, Quán, day,
   scenario và toàn bộ fixture test đổi cùng lúc; `main` không có trạng thái nửa vời.
3. Lưu độ tươi bằng số thực: đơn giản nhưng có rủi ro lệch nhánh ở ngưỡng 30 và phép floor khi chốt giá.

## Quyết định
- Chọn **phương án 2**: contract chỉ khai một phiên bản ("1.2"); bên đọc v1.2 trả mã 2 cho file kho đếm.
- Độ tươi bên trong là **phân số** (`fractions.Fraction`): hao 1/120 điểm/tick ở giỏ, 1/240 điểm/tick ở kho quán,
  so ngưỡng và floor giá chính xác. Ra ngoài: số nguyên nếu tròn, còn lại float; file kho ghi đủ độ chính xác
  (repr float), JSONL làm tròn 3 chữ số như mọi tọa độ.
- Id cá thể cấp từ một `IdAllocator` chung cho cả lượt (I1, I2… theo thứ tự vào giỏ, không cấp lại).

## Hệ quả — bảng tác động

| Module | File cần đổi | Test bị ảnh hưởng | Người phụ trách |
|---|---|---|---|
| Adapter / schema | `chonoi/inventory.py`, `chonoi/freshness.py` (mới), `game.contract.json`, `chonoi/contract.py` | `test_smoke_p1` (kho đếm → cá thể, thêm ca kho đếm cũ → mã 2), `test_phase2_rules::test_new_kinds_in_inventory_file` | Tanh0406 |
| Lặn | `chonoi/sim/gather.py` (giỏ cá thể, hao tươi, spoiled, lost cá thể) | `test_gather_rules` (faint.lost, hold, hold_full), `test_phase2_rules::Crocodile` | Tanh0406; rà: Người 1–4 |
| Quán | `chonoi/sim/quan.py` (kho cá thể, giữ theo id, giữ lại khi ươn, giá theo tươi) | `test_quan_rules` (giá 60 → 59 do chốt theo tươi), `test_quan_scenario`, `test_phase2_rules::QuanV11` | Tanh0406; rà: Người 5–6 |
| Scenario | `chonoi/scenario.py` (hold/stock mảng cá thể, reserved mảng id) | `test_quan_scenario` (thêm ca giữ sai loại / id lạ / hàng ươn / giữ trùng) | Tanh0406 |
| day | `chonoi/sim/day.py` (bàn giao cá thể, Shop không hao, id mới cho giỏ mẫu Ngày kế) | `test_day_mode` (stock là mảng cá thể) | Tanh0406 |
| HUD | `chonoi/web/index.html` (ô giỏ có số + thanh độ tươi, nhãn "ươn", kho khả dụng theo loại) | ảnh `docs/proof/phase-3/live-*.png` | Tanh0406 |
| QA | `tests/helpers.py` (`items`, `kinds_of`, `id_kind`), `tests/test_phase3_freshness.py` (mới) | toàn bộ regression P1–P2 chạy lại | QA lead |

**Thứ tự tích hợp (giữ `main` chạy được):** adapter + contract → Lặn → Quán → day → scenario → chuyển fixture
test (cùng một commit, test xanh) → HUD + tài liệu + bằng chứng (commit sau).
