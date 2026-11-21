---
name: sua-luat-kem-test
description: Quy trình cho agent khi sửa một luật trong chonoi/sim/*.py hoặc chonoi/scenario.py — đọc đúng mục PRD-0, viết test hộp đen tái hiện trước, sửa luật, chạy toàn bộ test rồi mới commit.
---

# Sửa luật kèm test hồi quy

1. **Đọc yêu cầu:** tìm câu tương ứng trong PRD-0 (mục D fixture, E event/snapshot, F thứ tự một bước) và `docs/contracts/README.md`. Chỗ mơ hồ: ghi `docs/clarify.md`, không tự bịa.
2. **Tái hiện bằng test hộp đen** trong `tests/test_gather_rules.py`, `tests/test_quan_rules.py` hoặc `tests/test_quan_scenario.py`:
   - dựng fixture nhỏ nhất (`random_fish: false` / `random_customers: false`, đặt vị trí ngay cạnh đối tượng);
   - dùng `--snapshot-every 1` khi cần so từng tick; so **chính xác** tick, id, số lượng, tiền, lý do; tọa độ ±0.1, uy tín ±0.01.
   - Chạy test, xác nhận nó **đỏ** trước khi sửa.
3. **Sửa luật** ở đúng chỗ, giữ thứ tự bước của mục F; số liệu chỉ đọc từ `game.contract.json`; ngẫu nhiên chỉ qua `Streams`.
4. **Chạy toàn bộ:** `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` — phải xanh hết, kể cả test tất định (cùng seed → cùng byte).
5. **Commit** một việc / một commit: mô tả luật đã sửa + tên test mới + số test đã chạy. Không sửa test cũ cho xanh khi luật sai.
