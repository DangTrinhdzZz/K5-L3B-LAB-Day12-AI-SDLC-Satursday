# Quán Ăn Chợ Nổi v1.0.2 — nhóm Satursday

Bản sửa lỗi cho v1.0.1. Gameplay, contract (**v1.3**), file kho và cách chạy giữ nguyên; sửa nốt các luật chưa đúng
PRD-0 / Ticket-02 / Ticket-03. **Không còn lỗi đã biết.**

## Cách chạy (Python 3.10+, không cài thêm gì)

```bash
git clone https://github.com/DangTrinhdzZz/K5-L3B-LAB-Day12-AI-SDLC-Satursday.git
cd K5-L3B-LAB-Day12-AI-SDLC-Satursday
python3 -m chonoi.live --mode day      # mở địa chỉ in ra (mặc định http://127.0.0.1:8000/)
```

Hoặc giải nén `quan-an-cho-noi-v1.0.2.zip` đính kèm Release, `cd` vào thư mục rồi chạy lệnh cuối ở trên.

## Đã sửa
| Phần | Luật đúng | Người làm |
|---|---|---|
| Quán | Boa khi tỷ lệ kiên nhẫn còn lại đúng 0.5 | Tanh0406 |
| Quán | Kẹp uy tín trong [0, 5] khi cộng `tip_reputation` | Tanh0406 |
| Quán | Tiền / earned cộng cả boa | Tanh0406 |
| Shop | Đủ đúng giá vẫn mua được | Tanh0406 + Vũ Tuấn Đạt (datkunal) |
| Giữ chỗ | Chọn cá thể chưa ươn tươi nhất, hòa theo id (lỗi đã biết của v1.0.1) | Tanh0406 + Vũ Tuấn Đạt (datkunal) |

## Kiểm chứng
- `PYTHONPATH=tests:. python3 -m unittest discover -s tests` → 139 test OK (skipped=1: bench thật).
- Bench, soak 10 Ngày, clone sạch chạy lại sau khi sửa: `docs/proof/phase-4/`.

Chi tiết: [`CHANGELOG.md`](../CHANGELOG.md). Bản trước: [`release-notes-v1.0.1.md`](release-notes-v1.0.1.md).
