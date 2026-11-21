# Hợp đồng tích hợp (chốt ở kickoff Phase 1)

Đổi bất kỳ mục nào dưới đây: báo cả nhóm trong kênh và ghi lý do (ADR trong `docs/adr/` nếu ảnh hưởng nhiều module).

## 1. File kho (gather → quan), PRD-0 mục G

```json
{"items": {"bong_sung": 2, "ca_loc": 1}}
```

- Chỉ có khóa gốc `items`: object `kind → số nguyên ≥ 0`. Kind hợp lệ: `ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung`.
- Bên ghi bỏ khóa có lượng 0, sắp khóa theo tên. Kho rỗng: `{"items":{}}`. Trần giỏ không áp lên kho quán.
- `gather --inventory-out` ghi **đúng một lần** khi có `gather_end`, nội dung khớp `gather_end.data.inventory`. Ngất thì ghi kho rỗng. Chạm `--ticks` trước khi kết thúc thì không tạo / không ghi đè file. Ghi file tạm cùng thư mục rồi thay thế nguyên tử (`chonoi/inventory.py`).
- `quan --inventory` đọc và từ chối sai schema, kind lạ, số âm → mã 2. Không được dùng cùng `scenario.quan.stock`.
- Ví dụ hợp lệ: [`inventory.sample.json`](inventory.sample.json).

## 2. Giao diện sim ↔ UI (`chonoi/sim/*` ↔ `chonoi/web/index.html`)

- UI **chỉ đọc** snapshot qua `GET /state` (cùng trường với dòng snapshot của headless, thêm `meta` = tuning của mode, `events` = 40 event gần nhất, `finished`, `reason`, `error`).
- UI **chỉ gửi** trạng thái phím qua `POST /input` `{"move":[a,b], "interact":bool, "catch":bool}`; `POST /restart` chơi lại.
- Sim không biết gì về UI; mọi luật nằm trong `sim/*`, UI không tự tính luật (riêng "kho khả dụng" trên HUD = `stock − Σ customers[].reserved`, chỉ để hiển thị).

| Mode | Trường UI đọc |
|---|---|
| chung | `tick`, `time_left_ticks`, `money`, `earned`, `reputation`, `score`, `state` |
| gather | `player{pos, vel, heading_deg, oxygen_ticks, oxygen_max_ticks, hp, hp_max, zero_oxy_ticks, catch_cd_ticks, at_surface}`, `hold`, `hold_count`, `hold_capacity`, `nodes[]{id,kind,pos,ready,regrow_ticks}`, `fish[]{id,kind,pos,heading_deg}` |
| quan | `player{pos, vel}`, `stock`, `hand`, `stoves[]{id,pos,state,dish,cook_ticks_left,ready_ticks}`, `tables[]{id,pos,customer_id}`, `customers[]{id,table_id,dish_id,order_tick,state,patience_ticks_left,eat_ticks_left,order_status,reserved,base_price,tip}` |

Payload món (trên bếp `dish` và `hand`): `{"order_id", "dish_id", "base_price"}`, `order_id` = id khách.

## 3. Sự kiện (PRD-0 mục E)

| Tên | `data` | Ai phát |
|---|---|---|
| `gather` | `node_id, kind, amount` | gather (lát 2) |
| `node_regrown` | `node_id` | gather (khung) |
| `hold_full` | `action` (`gather`/`catch`), `node_id` hoặc `fish_id`, `required`, `free` | gather (lát 2) |
| `fish_caught` | `fish_id, kind, yield` | gather (lát 2) |
| `dive` / `surface` | `pos` sau di chuyển | gather (lát 1) |
| `oxygen_empty` | `oxygen_ticks: 0` | gather (lát 1) |
| `choke` | `hp` sau khi trừ | gather (lát 1) |
| `faint` | `cause: "choke", lost` (mảng kind, LIFO), `hp: 0` | gather (lát 1) |
| `gather_end` | `reason` (`time`/`docked`/`fainted`), `inventory` theo mục 1 | gather |
| `customer_arrived` | `order_id, table_id, dish_id` | quan (lát 3) |
| `no_dish` | `{}` | quan (lát 3) |
| `cook_started` | `stove_id, order_id, dish_id, items` (mảng kind sắp theo kind), `base_price` | quan (lát 4) |
| `dish_ready` / `dish_picked` | `stove_id, order_id, dish_id` | quan (lát 4) |
| `served` | `order_id, table_id, dish_id, patience_ticks_left, base_price, tip` | quan (lát 4) |
| `paid` | `order_id, table_id, base_price, tip, amount, reason` (`finished_eating`/`closing`) | quan (lát 4) |
| `customer_left` | `order_id, table_id, reason` (`patience`/`closing`), `reputation` sau thay đổi | quan (lát 3) |
| `quan_end` | `reason: "time", money, earned, shift_earned, reputation` | quan |

Người nghe: runner ghi JSONL theo thứ tự xử lý; UI hiển thị 6 event cuối.
