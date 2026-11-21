"""Nạp và kiểm scenario (Contract D). Trả về dict của đúng khối theo mode.

KHUNG: kiểm cú pháp, id trùng, bộ đếm âm, khoang vượt sức chứa, trường lạ.
Nhóm: kiểm mâu thuẫn mức luật của quán theo PRD-0 mục D (đơn assigned có đúng một món, khách eating
có giá/tip, giữ chỗ đúng công thức...). Phần "giữ quá tồn" cần kho thật nên kiểm lúc dựng QuanSim.
"""

import json

from .errors import BadInput
from .inventory import KINDS_P1, validate_items

GATHER_KEYS = {"player", "hold", "nodes", "fish", "random_fish", "time_left_ticks"}
GATHER_PLAYER_KEYS = {"pos", "vel", "heading_deg", "hp", "oxygen_ticks", "zero_oxy_ticks",
                      "invuln_ticks", "catch_cd_ticks"}
NODE_KINDS = ("bong_dien_dien", "bong_sung")
FISH_KINDS = ("ca_linh", "ca_loc")
QUAN_PLAYER_KEYS = {"pos", "vel"}
QUAN_KEYS = {"player", "stock", "hand", "stoves", "tables", "customers", "random_customers",
             "reputation", "time_left_ticks"}


def _check_ids(name, arr):
    if not isinstance(arr, list):
        raise BadInput(f"{name} phải là mảng")
    seen = set()
    for e in arr:
        if not isinstance(e, dict) or not isinstance(e.get("id"), str) or not e["id"]:
            raise BadInput(f"{name}: mỗi phần tử cần id (chuỗi khác rỗng)")
        if e["id"] in seen:
            raise BadInput(f"{name}: id trùng {e['id']}")
        seen.add(e["id"])


def load_scenario(path, mode: str, tuning: dict) -> dict:
    if path is None:
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được scenario {path}: {e}")
    if not isinstance(data, dict) or not set(data) <= {"gather", "quan"}:
        raise BadInput("scenario chỉ được có khối 'gather' hoặc 'quan'")
    if set(data) - {mode}:
        raise BadInput(f"khối sai mode: chạy --mode {mode} chỉ nhận khối '{mode}'")
    block = data.get(mode, {})
    if not isinstance(block, dict):
        raise BadInput(f"khối {mode} phải là object")
    allowed = GATHER_KEYS if mode == "gather" else QUAN_KEYS
    extra = set(block) - allowed
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong {mode}: {sorted(extra)}")
    dur = int(round(tuning[mode]["duration_s"] * 60))
    if "time_left_ticks" in block:
        t = block["time_left_ticks"]
        if isinstance(t, bool) or not isinstance(t, int) or not (1 <= t <= dur):
            raise BadInput(f"time_left_ticks phải là số nguyên trong [1, {dur}]")
    if mode == "gather":
        _validate_gather(block, tuning)
    else:
        _validate_quan(block, tuning)
    return block


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _nonneg_int(name, v):
    if isinstance(v, bool) or not isinstance(v, int) or v < 0:
        raise BadInput(f"{name} phải là số nguyên không âm")


def _pos(name, pos, bounds, axes=("x", "d")):
    if not (isinstance(pos, list) and len(pos) == 2 and all(_num(c) for c in pos)):
        raise BadInput(f"{name} phải là [{axes[0]}, {axes[1]}]")
    for c, axis in zip(pos, axes):
        lo, hi = bounds[axis]
        if not (lo <= c <= hi):
            raise BadInput(f"{name} nằm ngoài vùng nước ({axis} ∈ [{lo}, {hi}])")


def _validate_gather(b, tuning):
    g = tuning["gather"]
    bounds = g["bounds"]
    for arr in ("nodes", "fish"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "random_fish" in b and not isinstance(b["random_fish"], bool):
        raise BadInput("random_fish phải là boolean")
    if "hold" in b:
        h = b["hold"]
        if not isinstance(h, list) or any(k not in KINDS_P1 for k in h):
            raise BadInput("hold phải là mảng id nguyên liệu hợp lệ")
        if len(h) > g["hold_capacity"]:
            raise BadInput("hold vượt sức chứa")
    p = b.get("player", {})
    if not isinstance(p, dict):
        raise BadInput("player phải là object")
    extra = set(p) - GATHER_PLAYER_KEYS
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong gather.player: {sorted(extra)}")
    if "pos" in p:
        _pos("player.pos", p["pos"], bounds)
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, d]")
    if "heading_deg" in p and not _num(p["heading_deg"]):
        raise BadInput("player.heading_deg phải là số")
    for key in ("invuln_ticks", "catch_cd_ticks", "zero_oxy_ticks", "oxygen_ticks", "hp"):
        if key in p:
            _nonneg_int(f"player.{key}", p[key])
    omax = int(round(g["oxygen_max_s"] * 60))
    if "oxygen_ticks" in p and p["oxygen_ticks"] > omax:
        raise BadInput("player.oxygen_ticks vượt oxy tối đa")
    if "hp" in p and not (1 <= p["hp"] <= g["hp_max"]):
        raise BadInput("player.hp phải trong [1, hp_max]")
    if "zero_oxy_ticks" in p:
        pos = p.get("pos", g["start_pos"])
        oxy = p.get("oxygen_ticks", omax)
        if p["zero_oxy_ticks"] > 59:
            raise BadInput("player.zero_oxy_ticks phải trong [0, 59]")
        if p["zero_oxy_ticks"] > 0 and not (oxy == 0 and pos[1] > g["surface_depth"]):
            raise BadInput("player.zero_oxy_ticks > 0 chỉ khi oxy = 0 và đang dưới nước")
    for n in b.get("nodes", []):
        if n.get("kind") not in NODE_KINDS:
            raise BadInput(f"nodes.{n['id']}: kind phải là một trong {NODE_KINDS}")
        _pos(f"nodes.{n['id']}.pos", n.get("pos"), bounds)
        if n["pos"][1] != 0:
            raise BadInput(f"nodes.{n['id']}: nút hái nằm ở mặt nước (d = 0)")
        if "regrow_ticks" in n:
            _nonneg_int(f"nodes.{n['id']}.regrow_ticks", n["regrow_ticks"])
    for f in b.get("fish", []):
        if f.get("kind") not in FISH_KINDS:
            raise BadInput(f"fish.{f['id']}: kind phải là một trong {FISH_KINDS}")
        _pos(f"fish.{f['id']}.pos", f.get("pos"), bounds)
        if f["pos"][1] <= g["surface_depth"]:
            raise BadInput(f"fish.{f['id']}: đàn cá phải ở dưới nước")
        if "heading_deg" in f and not _num(f["heading_deg"]):
            raise BadInput(f"fish.{f['id']}.heading_deg phải là số")


QUAN_CUSTOMER_KEYS = {"id", "table_id", "dish_id", "order_tick", "state", "patience_ticks_left", "eat_ticks_left",
                      "order_status", "reserved", "base_price", "tip"}
STOVE_KEYS = {"id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks"}
TABLE_KEYS = {"id", "pos"}
PAYLOAD_KEYS = {"order_id", "dish_id", "base_price"}
ORDER_STATUSES = ("reserved", "assigned", "unfulfillable", "served")


def _pos_int(name, v):
    if isinstance(v, bool) or not isinstance(v, int) or v <= 0:
        raise BadInput(f"{name} phải là số nguyên dương")


def _payload(name, d, menu):
    if not isinstance(d, dict) or set(d) != PAYLOAD_KEYS:
        raise BadInput(f"{name} phải là payload món {{order_id, dish_id, base_price}}")
    if not isinstance(d["order_id"], str) or d["dish_id"] not in menu:
        raise BadInput(f"{name}: order_id/dish_id không hợp lệ")
    _pos_int(f"{name}.base_price", d["base_price"])


def _validate_stoves_tables(b, q, menu, payloads):
    qb = q["bounds"]
    known_stoves = {s["id"] for s in q["stoves"]}
    known_tables = {t["id"] for t in q["tables"]}
    for s in b.get("stoves", []):
        sid = s["id"]
        if set(s) - STOVE_KEYS:
            raise BadInput(f"stoves.{sid}: trường lạ {sorted(set(s) - STOVE_KEYS)}")
        if sid not in known_stoves:
            raise BadInput(f"stoves.{sid}: id bếp không tồn tại")
        if "pos" in s:
            _pos(f"stoves.{sid}.pos", s["pos"], qb, axes=("x", "z"))
        state = s.get("state", "idle")
        if state not in ("idle", "cooking", "ready"):
            raise BadInput(f"stoves.{sid}.state phải là idle/cooking/ready")
        for key in ("cook_ticks_left", "ready_ticks"):
            if key in s:
                _nonneg_int(f"stoves.{sid}.{key}", s[key])
        cook, age, dish = s.get("cook_ticks_left", 0), s.get("ready_ticks", 0), s.get("dish")
        if state == "idle":
            if dish is not None or cook or age:
                raise BadInput(f"stoves.{sid}: bếp idle không có món / bộ đếm")
            continue
        _payload(f"stoves.{sid}.dish", dish, menu)
        if state == "cooking" and (cook <= 0 or age):
            raise BadInput(f"stoves.{sid}: bếp cooking cần cook_ticks_left dương")
        if state == "ready" and cook:
            raise BadInput(f"stoves.{sid}: bếp ready không còn cook_ticks_left")
        payloads.append((f"stoves.{sid}", dish))
    for t in b.get("tables", []):
        if set(t) - TABLE_KEYS:
            raise BadInput(f"tables.{t['id']}: trường lạ {sorted(set(t) - TABLE_KEYS)}")
        if t["id"] not in known_tables:
            raise BadInput(f"tables.{t['id']}: id bàn không tồn tại")
        if "pos" in t:
            _pos(f"tables.{t['id']}.pos", t["pos"], qb, axes=("x", "z"))
    return known_tables


def _validate_customer(c, q, menu, known_tables):
    cid = c["id"]
    full_pat = int(round(q["patience_s"] * 60))
    full_eat = int(round(q["eat_s"] * 60))
    if set(c) - QUAN_CUSTOMER_KEYS:
        raise BadInput(f"customers.{cid}: trường lạ {sorted(set(c) - QUAN_CUSTOMER_KEYS)}")
    if not isinstance(c.get("table_id"), str) or c["table_id"] not in known_tables:
        raise BadInput(f"customers.{cid}: table_id phải là bàn có thật")
    if c.get("dish_id") not in menu:
        raise BadInput(f"customers.{cid}: dish_id phải là món trong menu")
    state = c.get("state", "waiting")
    status = c.get("order_status", "reserved")
    if state not in ("waiting", "eating") or status not in ORDER_STATUSES:
        raise BadInput(f"customers.{cid}: state/order_status không hợp lệ")
    for key in ("order_tick", "patience_ticks_left", "eat_ticks_left"):
        if key in c:
            _nonneg_int(f"customers.{cid}.{key}", c[key])
    eat = c.get("eat_ticks_left", 0)
    if c.get("patience_ticks_left", full_pat) > full_pat or eat > full_eat:
        raise BadInput(f"customers.{cid}: kiên nhẫn / timer ăn vượt mức đầy")
    res = c.get("reserved", {})
    if not isinstance(res, dict):
        raise BadInput(f"customers.{cid}.reserved phải là object")
    for k, n in res.items():
        if k not in KINDS_P1 or isinstance(n, bool) or not isinstance(n, int) or n <= 0:
            raise BadInput(f"customers.{cid}.reserved: {k} không hợp lệ")
    if c.get("base_price") is not None:
        _pos_int(f"customers.{cid}.base_price", c["base_price"])
    if c.get("tip") is not None:
        _nonneg_int(f"customers.{cid}.tip", c["tip"])
    if status == "reserved" and "reserved" in c and res != menu[c["dish_id"]]["recipe"]:
        raise BadInput(f"customers.{cid}: giữ chỗ khác công thức món")
    if status != "reserved" and res:
        raise BadInput(f"customers.{cid}: đơn {status} không còn giữ chỗ")
    if state == "eating":
        if status != "served" or eat <= 0 or c.get("base_price") is None or c.get("tip") is None:
            raise BadInput(f"customers.{cid}: khách eating phải served, timer ăn dương, có base_price và tip")
    elif status == "served" or eat:
        raise BadInput(f"customers.{cid}: khách waiting không thể served / có timer ăn")
    return dict(c, state=state, order_status=status)


def _validate_quan(b, tuning):
    """Kiểm fixture quán theo PRD-0 mục D (mâu thuẫn -> mã 2). Phần so với kho (quá tồn) kiểm lúc dựng sim."""
    q, menu = tuning["quan"], tuning["menu"]
    for arr in ("stoves", "tables", "customers"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "stock" in b:
        validate_items(b["stock"])
    if "random_customers" in b and not isinstance(b["random_customers"], bool):
        raise BadInput("random_customers phải là boolean")
    if "reputation" in b:
        r = b["reputation"]
        if not _num(r) or not (q["reputation_min"] <= r <= q["reputation_max"]):
            raise BadInput(f"reputation phải trong [{q['reputation_min']}, {q['reputation_max']}]")
    p = b.get("player", {})
    if not isinstance(p, dict) or set(p) - QUAN_PLAYER_KEYS:
        raise BadInput("quan.player chỉ có pos và vel")
    if "pos" in p:
        _pos("player.pos", p["pos"], q["bounds"], axes=("x", "z"))
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, z]")
    payloads = []  # (nơi giữ, payload món)
    known_tables = _validate_stoves_tables(b, q, menu, payloads)
    if b.get("hand") is not None:
        _payload("hand", b["hand"], menu)
        payloads.append(("hand", b["hand"]))
    customers = b.get("customers", [])
    by_id = {c["id"]: _validate_customer(c, q, menu, known_tables) for c in customers}
    table_ids = [c["table_id"] for c in customers]
    if len(table_ids) != len(set(table_ids)):
        raise BadInput("hai khách cùng bàn")
    # liên kết món <-> đơn: đơn assigned có đúng một món ở bếp hoặc tay, khớp dish_id
    held = {}
    for where, d in payloads:
        c = by_id.get(d["order_id"])
        if c is None or c["order_status"] != "assigned" or c["dish_id"] != d["dish_id"]:
            raise BadInput(f"{where}: món không khớp đơn assigned nào")
        if d["order_id"] in held:
            raise BadInput(f"{where} và {held[d['order_id']]} giữ cùng đơn {d['order_id']}")
        held[d["order_id"]] = where
    for cid, c in by_id.items():
        if c["order_status"] == "assigned" and cid not in held:
            raise BadInput(f"customers.{cid}: đơn assigned phải có đúng một món ở bếp hoặc trên tay")
