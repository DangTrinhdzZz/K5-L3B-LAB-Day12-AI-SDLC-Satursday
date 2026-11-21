# AGENTS.md — hướng dẫn chung cho mọi agent AI của nhóm

> Cập nhật file này qua các phase (lịch sử git phải cho thấy điều đó). Ngắn gọn, có lệnh chạy thật.

## Lệnh
- Test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
- Headless: `python3 -m chonoi.headless --mode gather|quan|day --seed 1 --ticks 600 --out out.jsonl` (day thêm `--days 1..5`)
- Benchmark: `python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json` (cần Chrome/Chromium; test bench thật: `CHONOI_RUN_BENCH=1`)
- Soak: `python3 -m chonoi.soak --seed 7 --days 10 --out soak.json` · Đóng gói: `python3 tools/package.py v1.0.0`
- Chơi thử trên trình duyệt: `python3 -m chonoi.live --mode day|gather|quan` (mở địa chỉ in ra; WASD, E, Space, Esc/P, 1/2/Enter trong Shop, R)

## Cấu trúc & quy ước
- (Starter Python là TÙY CHỌN; nhóm có thể dùng ngôn ngữ khác nếu giữ Test Contract.) Khung do giảng viên cấp: `chonoi/{headless,inputs,scenario,contract,rng,ids,jsonl,inventory,runner,live}.py` và `chonoi/web/`. Hạn chế sửa; nếu phải sửa thì báo cả nhóm và ghi lại lý do.
- Luật chơi của nhóm: `chonoi/sim/gather.py` (lát 1–2) + `fish.py` (cá bơi/sinh) + `monsters.py` (Cá Sấu), `chonoi/sim/quan.py` (lát 3–4), `chonoi/sim/day.py` (vòng ngày, Shop); pause và bộ đếm tick ở `chonoi/runner.py`; kiểm fixture ở `chonoi/scenario.py`.
- Contract v1.2: kho là mảng CÁ THỂ `{id, kind, fresh}` (độ tươi tính bằng phân số trong `chonoi/freshness.py`);
  fixture test dựng bằng `items(...)` ở `tests/helpers.py`; không dùng lại kho đếm `{kind: n}`.
- Mọi số (kể cả day_plan, shop, freshness) chỉ trong `game.contract.json`; đổi luật thì cập nhật cấu hình, spec (`docs/contracts/`) và test cùng commit.
- Test của nhóm: `tests/test_gather_rules.py`, `tests/test_quan_rules.py`, `tests/test_quan_scenario.py`, `tests/test_phase2_rules.py`, `tests/test_day_mode.py`, `tests/test_phase3_freshness.py` (hộp đen qua `headless_cmd`).
- Hợp đồng kho + sự kiện + giao diện sim/UI: `docs/contracts/README.md`.
- **Số liệu chỉ đọc từ `game.contract.json` / dữ liệu**, không hard-code trong luật.
- Mọi số ngẫu nhiên đi qua `Streams` (`chonoi/rng.py`); không dùng `random` toàn cục, không dùng đồng hồ hệ thống.
- Sắp danh sách thực thể bằng `ids.sort_by_id`; cấp id bằng `IdAllocator`.

## Nên tránh
- Không sửa `docs/contracts/`, `game.contract.json` (khóa contract) hoặc schema kho khi chưa báo cả nhóm (đổi hợp đồng ảnh hưởng mọi module).
- Không làm hỏng nhánh chính: trước khi đẩy, chạy test.
- Không bịa yêu cầu: chỗ mơ hồ thì ghi `docs/clarify.md` và hỏi PO.
- Không sửa test cho xanh khi luật sai; phải sửa luật hoặc ghi lý do đổi test trong commit.

## Quy tắc làm việc với agent
- Mỗi agent một việc rõ ràng (một lát). Cho agent đọc PRD/ticket đúng phase và hợp đồng kho trước.
- Agent làm xong phải chạy test và ghi kết quả vào mô tả commit hoặc `docs/proof/`; người đọc lại thay đổi trước khi đẩy.
- Sáng tạo thêm được khuyến khích nhưng phải tắt ở headless (xem README, mục "Tự do sáng tạo").

## Skills / hooks của nhóm
- `.agents/skills/sua-luat-kem-test/SKILL.md` — mỗi lần sửa luật trong `sim/*` hoặc `scenario.py`: test tái hiện đỏ trước, sửa, chạy toàn bộ test.
- `.agents/skills/smoke-hai-tien-trinh/SKILL.md` — trước khi gắn tag phase: chạy smoke gather → kho → quan, lưu bằng chứng vào `docs/proof/phase-n/`.
- Windows: đặt `PYTHONUTF8=1` (và `PYTHONPATH=tests;.`) để stderr tiếng Việt không lỗi mã hóa.
