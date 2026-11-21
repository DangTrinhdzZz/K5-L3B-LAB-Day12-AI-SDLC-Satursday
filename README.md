# Quán Ăn Chợ Nổi — nhóm Satursday

> Day 12 · AI SDLC · K5-L3B. Út Sen lặn bắt cá, hái bông trên sông Chín Khúc buổi sáng, tối mở quán trên nhà bè của Má Tư.
> Đề bài và lịch phase: **[Chợ Nổi Lab](https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg)** · Thành viên và vai: [`TEAM.md`](TEAM.md).

## Chạy từ clone sạch (macOS / Linux, chỉ cần Python 3.10+)

```bash
git clone https://github.com/DangTrinhdzZz/K5-L3B-LAB-Day12-AI-SDLC-Satursday.git && cd K5-L3B-LAB-Day12-AI-SDLC-Satursday
python3 -m chonoi.live --mode gather --inventory-out kho.json   # buổi sáng: mở địa chỉ in ra trên trình duyệt
python3 -m chonoi.live --mode quan --inventory kho.json         # buổi tối: quán đọc kho vừa mang về
```

Không cần cài thêm gì (chỉ thư viện chuẩn Python). `build_cmd` là `true`.

**Test của nhóm (1 lệnh):**

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
```

**Headless (Test Contract v1.0):** `python3 -m chonoi.headless --mode gather|quan --seed <int> --ticks <N> --out out.jsonl [--scenario sc.json] [--inputs in.json] [--inventory kho.json] [--inventory-out kho.json] [--snapshot-every N]`

## Điều khiển

| Phím | Buổi sáng (gather) | Buổi tối (quan) |
|---|---|---|
| WASD / mũi tên | bơi ngang, lặn xuống / nổi lên | đi trong nhà bè |
| **E** (`interact`) | cập bến (trong vùng bến) hoặc hái nút ở mặt nước | nấu ở bếp, bưng món chín, phục vụ ở bàn |
| **Space** (`catch`) | bắt đàn cá gần nhất khi đang lặn | — |
| **R** | chơi lại | chơi lại |

HUD buổi sáng: thời gian, thanh oxy, Máu (♥), giỏ `n/12`. HUD buổi tối: thời gian, tiền, uy tín, điểm, kho khả dụng/tồn, món khách gọi + kiên nhẫn, trạng thái bếp, món trên tay.

## Luật tóm tắt

- **Sáng:** dưới nước (d > 0.5) mất 1 tick oxy mỗi tick, ở mặt nước hồi 6 tick/tick. Oxy 0 liên tục 60 tick thì ngạt, mất 1 Máu; hết 3 Máu thì ngất, mất cả giỏ. Hái nút ở mặt nước (mọc lại sau 20 s), bắt đàn cá khi lặn (cá linh ×3, cá lóc ×1, hồi chiêu 0.5 s). Giỏ chứa 12. Cập bến hoặc hết 180 s thì mang giỏ về kho.
- **Tối:** khách đến từ tick 120, rồi mỗi 15 s; gọi món nấu được với kho khả dụng và giữ chỗ nguyên liệu. Nấu ở bếp B1 → bưng → phục vụ bàn T1 trước khi hết 60 s kiên nhẫn. Ăn 10 s rồi trả tiền; còn ≥ 50 % kiên nhẫn khi được phục vụ thì boa `floor(20 % giá)` và +0.2 uy tín. Khách bỏ đi vì hết kiên nhẫn: −0.5 uy tín. Uy tín kẹp trong [0, 5].
- Món: cá lóc nướng trui (cá lóc ×1, 6 s, 60k) · gỏi bông súng (bông súng ×2, 4 s, 40k) · lẩu cá linh bông điên điển (cá linh ×3 + điên điển ×1, 10 s, 120k).

## Cách tính điểm

`score = earned + 100 × floor(reputation)`. `earned` là tổng tiền thu cả lượt (nghìn đồng, gồm boa), `reputation` là uy tín hiện tại. Điểm có ở mọi snapshot và dòng `end`.

## Hợp đồng tích hợp

File kho giữa hai buổi, danh sách sự kiện và giao diện sim ↔ UI: [`docs/contracts/README.md`](docs/contracts/README.md) (ví dụ hợp lệ: [`inventory.sample.json`](docs/contracts/inventory.sample.json)).

## Cấu trúc

| Đường dẫn | Nội dung |
|---|---|
| `chonoi/sim/gather.py` | luật buổi sáng (lát 1–2) |
| `chonoi/sim/quan.py` | luật buổi tối (lát 3–4) |
| `chonoi/scenario.py` | đọc + kiểm fixture (mâu thuẫn → mã 2) |
| `chonoi/web/index.html`, `chonoi/live.py` | cửa sổ chơi trên trình duyệt + HUD |
| `chonoi/{headless,runner,inputs,contract,inventory,jsonl,rng,ids}.py` | khung Test Contract của giảng viên |
| `tests/` | smoke hộp đen + test luật của nhóm |
| `docs/` | hợp đồng, kế hoạch, kiểm chứng, bằng chứng, clarify, nhật ký AI, retro |

## Sáng tạo của nhóm

(Chưa có. Khi thêm, ghi ý tưởng ở đây kèm bằng chứng lõi headless vẫn đúng.)
