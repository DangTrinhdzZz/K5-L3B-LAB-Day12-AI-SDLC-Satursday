# Kế hoạch Phase 1 (≤ 1 trang)

- **Mục tiêu:** chơi được buổi sáng (gather) và buổi tối (quan) đúng lõi PRD-0, nối nhau qua file kho; headless đúng Test Contract v1.0; HUD đọc được; tag `phase-1` trước 1:00.
- **Hợp đồng chốt trước:** `docs/contracts/README.md` (kho, sự kiện, giao diện sim ↔ UI) — Integrator giữ.

| Việc | AC | Người | Phụ thuộc |
|---|---|---|---|
| Lát 1: oxy, ngạt, Máu, ngất, dive/surface | AC-P1-01..04 | Tanh0406 → rà/sửa: lát 1 | hợp đồng sự kiện |
| Lát 2: hái nút, bắt cá, hold_full, cập bến, kho | AC-P1-05..08 | Tanh0406 → rà/sửa: lát 2 | lát 1 (at_surface) |
| Lát 3: khách theo lịch, giữ chỗ, kiên nhẫn, no_dish | AC-P1-09..11 | Tanh0406 → rà/sửa: lát 3 | kho mẫu |
| Lát 4: bếp, bưng, phục vụ, boa, tiền, uy tín, quan_end | AC-P1-12..15 | Tanh0406 → rà/sửa: lát 4 | lát 3 |
| Kiểm fixture quán (mã 2) | AC-P1-16 | Tanh0406 | lát 3–4 |
| HUD buổi sáng / tối | AC-P1-17 | client/ui | snapshot |
| Smoke hai tiến trình + ma trận truy vết | AC-P1-18 | QA lead | tất cả |

- **Rủi ro:** PRD dài, nhiều chi tiết biên (đúng mép bán kính, đúng tick ngạt/boa) → mỗi lát rà lại theo mục F và viết test hồi quy; nhiều người cùng sửa `gather.py`/`quan.py` → commit nhỏ, `pull --rebase` thường xuyên.
