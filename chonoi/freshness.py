"""Độ tươi của cá thể nguyên liệu (Ticket-03, contract v1.2).

Cá thể: {"id": "I7", "kind": "ca_linh", "fresh": Fraction}. Bên trong dùng phân số để phép so ngưỡng 30 và phép floor
khi chốt giá luôn chính xác (0.5/s ở giỏ = 1/120 điểm mỗi tick, 0.25/s ở kho quán = 1/240 điểm mỗi tick).
Ra ngoài (snapshot, event, file kho) đổi về số: nguyên nếu tròn, còn lại là float (JSONL làm tròn 3 chữ số khi xuất;
file kho ghi đủ độ chính xác để đọc lại giữ đúng nhánh ở ngưỡng).
"""

import math
from fractions import Fraction

from .ids import id_key, sort_by_id

TICK_HZ = 60


def frac(v) -> Fraction:
    return v if isinstance(v, Fraction) else Fraction(v)


def out_num(f):
    f = frac(f)
    return int(f) if f.denominator == 1 else float(f)


def item_out(it) -> dict:
    return {"id": it["id"], "kind": it["kind"], "fresh": out_num(it["fresh"])}


def make_item(item_id, kind, fresh) -> dict:
    return {"id": item_id, "kind": kind, "fresh": frac(fresh)}


class Freshness:
    """Tham số độ tươi lấy từ tuning.freshness."""

    def __init__(self, tuning):
        f = tuning["freshness"]
        self.initial = frac(f["initial"])
        self.threshold = frac(f["spoiled_below"])
        self.gather_per_tick = frac(f["gather_decay_per_s"]) / TICK_HZ
        self.quan_per_tick = frac(f["quan_decay_per_s"]) / TICK_HZ

    def is_spoiled(self, it) -> bool:
        return frac(it["fresh"]) <= self.threshold

    def decay(self, items, per_tick, location):
        """Hao tươi một tick (kẹp đáy 0). Trả (events spoiled theo id, danh sách id vừa ươn)."""
        events, newly = [], []
        for it in sort_by_id(items):
            was_ok = not self.is_spoiled(it)
            it["fresh"] = max(Fraction(0), it["fresh"] - per_tick)
            if was_ok and self.is_spoiled(it):
                newly.append(it["id"])
                events.append(("spoiled", {"item_id": it["id"], "kind": it["kind"], "location": location}))
        return events, newly

    def freshest(self, items, kind, n, exclude=()):
        """n cá thể chưa ươn của `kind` tươi nhất, hòa theo id; None nếu không đủ."""
        cands = [it for it in items if it["kind"] == kind and it["id"] not in exclude and not self.is_spoiled(it)]
        cands.sort(key=lambda it: id_key(it["id"]))
        return cands[:n] if len(cands) >= n else None


def locked_price(list_price, items) -> int:
    """floor(giá niêm yết × trung bình fresh / 100), tính chính xác bằng phân số."""
    avg = sum((frac(it["fresh"]) for it in items), Fraction(0)) / len(items)
    return math.floor(Fraction(list_price) * avg / 100)
