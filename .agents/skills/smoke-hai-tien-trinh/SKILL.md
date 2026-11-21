---
name: smoke-hai-tien-trinh
description: Chạy smoke test hộp đen gather → file kho → quan theo PRD-0 mục G và lưu bằng chứng vào docs/proof/phase-n/. Dùng trước khi gắn tag phase hoặc sau khi sửa luật gather/quan/kho.
---

# Smoke hai tiến trình (gather → kho → quan)

1. Từ gốc repo, tạo fixture (nếu chưa có) trong `docs/proof/phase-<n>/`:
   - `dock.json`: `{"gather":{"hold":["ca_loc","bong_sung","bong_sung"]}}`
   - `dock-inputs.json`: `{"frames":[{"tick":0,"interact":true}]}`
2. Chạy:
   ```bash
   P=docs/proof/phase-<n>
   python3 -m chonoi.headless --mode gather --seed 42 --scenario $P/dock.json --inputs $P/dock-inputs.json \
       --ticks 1 --out $P/gather.out.jsonl --inventory-out $P/catch.json
   python3 -m chonoi.headless --mode quan --seed 42 --inventory $P/catch.json --ticks 0 --out $P/quan.out.jsonl
   ```
3. Kiểm: cả hai lệnh mã thoát 0; `catch.json` là `{"items":{"bong_sung":2,"ca_loc":1}}`; dòng đầu `quan.out.jsonl` có `"stock":{"bong_sung":2,"ca_loc":1}`.
4. Ghi lệnh + đầu ra thật vào `$P/smoke-hai-tien-trinh.txt` (không sửa tay đầu ra), dẫn link từ `docs/verification/phase-<n>.md`.
5. Chạy toàn bộ test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`, lưu đuôi kết quả vào `$P/unittest.txt`.

Không bịa kết quả: test đỏ thì ghi "chưa đạt" và lý do.
