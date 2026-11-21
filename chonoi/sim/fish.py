"""Đàn cá bơi và sinh theo lịch (Ticket-02 mục 1.1, contract v1.1).

- Mỗi đàn: {id, kind, pos [x, d], heading_deg, age_ticks}. age_ticks = số bước đã tham gia bơi.
- Bơi fish_speed m/s trong x ∈ fish_x và d ∈ fish_depths[kind]. Ở bước bơi thứ fish_turn_ticks, 2·fish_turn_ticks…
  đổi hướng theo seed TRƯỚC khi di chuyển. Tới mép: phản xạ phần quãng đường còn lại và đảo thành phần hướng
  vuông góc với mép (chạm góc đảo cả hai).
- Sinh: tại phase_tick = fish_spawn_ticks·k (k ≥ 1), sau khi cá bơi, tối đa một đàn nếu còn dưới fish_max và còn
  điểm sinh cách mọi đàn đang sống > fish_spawn_clearance. Chọn loài theo fish_weights (chuẩn hóa lại theo loài còn
  điểm hợp lệ), rồi chọn đều một điểm của loài, hướng ban đầu theo seed. Đầu ca dùng cùng thủ tục cho fish_initial đàn.
Mọi ngẫu nhiên đi qua Streams: luồng "fish_spawn" (loài, điểm, hướng ban đầu) và "fish_turn" (đổi hướng).
"""

import math

from ..ids import sort_by_id
from ..inventory import FISH_KINDS

TICK = 60.0


def _spawn_points(t, kind):
    return [(float(x), float(d)) for x in t["fish_spawn_x"] for d in t["fish_spawn_depths"][kind]]


def _free_points(t, kind, fish):
    clear = t["fish_spawn_clearance"]
    return [p for p in _spawn_points(t, kind) if all(math.dist(p, f["pos"]) > clear for f in fish)]


def pick_spawn(t, fish, rng):
    """Chọn (kind, pos, heading) cho một đàn mới, hoặc None nếu hết điểm."""
    r = rng.get("fish_spawn")
    options = [(k, _free_points(t, k, fish)) for k in FISH_KINDS]
    options = [(k, pts) for k, pts in options if pts and t["fish_weights"][k] > 0]
    if not options:
        return None
    total = sum(t["fish_weights"][k] for k, _ in options)
    u = r.random() * total
    kind, pts = options[-1]
    for k, p in options:
        u -= t["fish_weights"][k]
        if u < 0:
            kind, pts = k, p
            break
    pos = r.choice(pts)
    heading = r.random() * 360.0
    return kind, [pos[0], pos[1]], heading


def initial_fish(t, rng, ids):
    fish = []
    for _ in range(t["fish_initial"]):
        got = pick_spawn(t, fish, rng)
        if got is None:
            break
        kind, pos, heading = got
        fish.append({"id": ids.new("F"), "kind": kind, "pos": pos, "heading_deg": heading, "age_ticks": 0})
    return fish


def _reflect(v, lo, hi):
    """Trả (vị trí mới, có đảo thành phần không)."""
    if v > hi:
        return hi - (v - hi), True
    if v < lo:
        return lo + (lo - v), True
    return v, False


def swim(t, fish, rng):
    """Một bước bơi cho mọi đàn, theo id."""
    step = t["fish_speed"] / TICK
    turn = t["fish_turn_ticks"]
    r = rng.get("fish_turn")
    xlo, xhi = t["fish_x"]
    for f in sort_by_id(fish):
        n = f["age_ticks"] + 1
        if n % turn == 0:
            f["heading_deg"] = r.random() * 360.0
        a = math.radians(f["heading_deg"])
        vx, vd = math.cos(a), math.sin(a)
        dlo, dhi = t["fish_depths"][f["kind"]]
        x, fx = _reflect(f["pos"][0] + vx * step, xlo, xhi)
        d, fd = _reflect(f["pos"][1] + vd * step, dlo, dhi)
        if fx:
            vd = -vd
        if fd:
            vd = -vd
        if fx or fd:
            f["heading_deg"] = math.degrees(math.atan2(vd, vx)) % 360.0
        f["pos"] = [x, d]
        f["age_ticks"] = n


def maybe_spawn(t, fish, rng, ids, phase_tick):
    """Sinh tối đa một đàn theo lịch; trả event fish_spawned hoặc None."""
    if phase_tick <= 0 or phase_tick % t["fish_spawn_ticks"] != 0 or len(fish) >= t["fish_max"]:
        return None
    got = pick_spawn(t, fish, rng)
    if got is None:
        return None
    kind, pos, heading = got
    f = {"id": ids.new("F"), "kind": kind, "pos": pos, "heading_deg": heading, "age_ticks": 0}
    fish.append(f)
    return ("fish_spawned", {"id": f["id"], "kind": kind, "pos": list(pos)})
