"""File kho (Contract G) — v1.2: kho CÁ THỂ {"items": [{"id", "kind", "fresh"}, ...]} (Ticket-03 mục 1).

Đọc: đúng khóa gốc `items`, giá trị là mảng cá thể; id chuỗi khác rỗng, duy nhất; kind thuộc danh mục; fresh hữu hạn
trong [0, 100]. File kho đếm của v1.0/v1.1 ({"items": {kind: n}}) -> BadInput (mã 2).
Ghi: sắp theo id, fresh đủ độ chính xác (float repr), qua file tạm cùng thư mục rồi thay thế nguyên tử, byte-ổn-định.
"""

import json
import math
import os
import tempfile

from .errors import BadInput
from .freshness import item_out
from .ids import sort_by_id

FISH_KINDS = ("ca_linh", "ca_loc", "ca_keo")
NODE_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")
KINDS = ("ca_loc", "ca_linh", "ca_keo", "bong_dien_dien", "bong_sung", "keo_neo")
KINDS_P1 = KINDS  # tên cũ, giữ để không vỡ chỗ đang import
ITEM_KEYS = {"id", "kind", "fresh"}


def validate_item_list(items, name="items", kinds=KINDS, seen=None) -> list:
    """Kiểm mảng cá thể; trả bản sao [{id, kind, fresh}] giữ nguyên thứ tự. `seen` gom id để kiểm trùng giữa nhiều nơi."""
    if not isinstance(items, list):
        raise BadInput(f"{name} phải là mảng cá thể {{id, kind, fresh}} (contract v1.2)")
    seen = set() if seen is None else seen
    out = []
    for i, it in enumerate(items):
        if not isinstance(it, dict) or set(it) != ITEM_KEYS:
            raise BadInput(f"{name}[{i}] phải có đúng các khóa id, kind, fresh")
        if not isinstance(it["id"], str) or not it["id"]:
            raise BadInput(f"{name}[{i}].id phải là chuỗi khác rỗng")
        if it["id"] in seen:
            raise BadInput(f"{name}: id cá thể trùng {it['id']}")
        seen.add(it["id"])
        if it["kind"] not in kinds:
            raise BadInput(f"{name}[{i}]: nguyên liệu lạ {it['kind']!r}")
        f = it["fresh"]
        if isinstance(f, bool) or not isinstance(f, (int, float)) or not math.isfinite(f) or not 0 <= f <= 100:
            raise BadInput(f"{name}[{i}].fresh phải là số hữu hạn trong [0, 100]")
        out.append({"id": it["id"], "kind": it["kind"], "fresh": f})
    return out


def read_inventory(path: str, kinds=KINDS) -> list:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    return validate_item_list(data["items"], "file kho items", kinds)


def inventory_payload(items) -> dict:
    """Object kho theo schema v1.2 (dùng cho gather_end.data.inventory và file kho)."""
    return {"items": [item_out(it) for it in sort_by_id(items)]}


def kind_counts(items) -> dict:
    counts = {}
    for it in items:
        counts[it["kind"]] = counts.get(it["kind"], 0) + 1
    return {k: counts[k] for k in sorted(counts)}


def write_inventory(path: str, items):
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(inventory_payload(items), f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
