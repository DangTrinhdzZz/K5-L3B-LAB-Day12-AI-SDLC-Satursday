"""Bảng xếp hạng cục bộ (mở rộng `leaderboard`, Ticket-04 mục 3).

Store: {"entries": [{"name", "score", "days_completed", "seed"}, ...]} — đã sắp: điểm giảm dần, hòa thì mục ghi
trước đứng trước (thứ tự trong file giữ nguyên khi mở lại). Chỉ giữ top 10. Ghi qua file tạm rồi thay thế nguyên tử.
Chỉ ghi cho lượt chuẩn: mode day đủ 5 Ngày, không scenario, kết thúc `days_complete`.
Store mặc định: $CHONOI_LEADERBOARD hoặc ~/.chonoi/leaderboard.json.
"""

import json
import os
import tempfile

from .errors import BadInput

TOP_N = 10
STANDARD_DAYS = 5
ENTRY_KEYS = ("name", "score", "days_completed", "seed")


def default_store() -> str:
    return os.environ.get("CHONOI_LEADERBOARD") or os.path.join(os.path.expanduser("~"), ".chonoi", "leaderboard.json")


def valid_name(name) -> bool:
    return isinstance(name, str) and name.strip() != ""


def load(path) -> list:
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được bảng xếp hạng {path}: {e}")
    entries = data.get("entries") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        raise BadInput("bảng xếp hạng phải có khóa entries (mảng)")
    for e in entries:
        if not isinstance(e, dict) or set(e) != set(ENTRY_KEYS) or not valid_name(e["name"]):
            raise BadInput("mục xếp hạng phải có name, score, days_completed, seed")
    return entries


def _save(path, entries):
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".lb-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"entries": entries}, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def add(path, name, score, days_completed, seed) -> list:
    """Chèn một mục (sau mọi mục có điểm >= điểm mới để giữ thứ tự ghi khi hòa), giữ top 10, trả bảng mới."""
    if not valid_name(name):
        raise BadInput("tên người chơi phải là chuỗi khác rỗng")
    entries = load(path)
    pos = next((i for i, e in enumerate(entries) if e["score"] < score), len(entries))
    entries.insert(pos, {"name": name, "score": score, "days_completed": days_completed, "seed": seed})
    entries = entries[:TOP_N]
    _save(path, entries)
    return entries


def export(store, out):
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"entries": load(store)}, f, ensure_ascii=False, indent=2)
        f.write("\n")
