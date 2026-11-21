"""Buổi tối — Mở Quán (`quan`). Nhìn từ trên xuống, vị trí `[x, z]`.

Thứ tự một bước theo PRD-0 mục F "Quán":
  1. Đồng hồ: tăng phase_tick, giảm timer ca, nấu, ăn, kiên nhẫn; ready_ticks chỉ tăng cho món đã ready đầu bước.
  2. Bếp theo id: nấu xong -> ready (dish_ready), ready_ticks = 0. burn_s = null (chưa có cháy).
  3. Đi lại rồi tối đa MỘT interact, chọn theo (khoảng cách, bếp trước bàn, id); không tương tác được thì bỏ lượt.
     - bếp idle: lấy đơn reserved cũ nhất (order_tick, id bàn), tiêu nguyên liệu giữ, chốt giá -> cook_started
     - bếp ready + tay trống -> dish_picked
     - bàn có khách chờ đúng order_id trên tay -> served (chốt boa)
  4. Theo id bàn: ăn xong -> paid; còn giờ: kiên nhẫn 0 -> customer_left(patience);
     hết ca: khách đang ăn trả ngay (closing), khách chờ rời (closing, không trừ uy tín) -> quan_end.
  5. Còn giờ: lượt khách theo first_customer_tick rồi mỗi customer_interval_s; bàn trống id nhỏ nhất;
     chọn đều theo seed trong các món đủ nguyên liệu khả dụng (tồn - giữ), không có -> no_dish.

Lát 3: khách, giữ chỗ nguyên liệu, kiên nhẫn. Lát 4: bếp, bưng, phục vụ, tiền, uy tín.
"""

import math

from ..errors import BadInput
from ..ids import id_key, sort_by_id
from .ramp import ramp_velocity

TICK = 60.0
REP_DIGITS = 9  # làm tròn uy tín sau mỗi lần cộng/trừ để floor(uy tín) không lệch do số thực


def _ticks(seconds) -> int:
    return int(round(seconds * TICK))


def _expand(counts: dict) -> list:
    """{kind: n} -> mảng kind sắp theo kind (dùng cho cook_started.items)."""
    out = []
    for k in sorted(counts):
        out.extend([k] * counts[k])
    return out


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None):
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2). Tồn vật lý, gồm cả phần giữ chỗ.
        self.stock = dict(inventory if inventory is not None else scenario.get("stock", {}))
        self.hand = dict(scenario["hand"]) if scenario.get("hand") else None
        self.time_left_ticks = scenario.get("time_left_ticks", _ticks(t["duration_s"]))
        self.reputation = float(scenario.get("reputation", t["reputation_initial"]))
        self.random_customers = scenario.get("random_customers", True)
        self.phase_tick = 0
        self.patience_full = _ticks(t["patience_s"])
        self.eat_full = _ticks(t["eat_s"])
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=dict(s["dish"]) if s.get("dish") else None,
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.customers = [self._fixture_customer(c) for c in scenario.get("customers", [])]
        for e in self.customers:
            ids.reserve(e["id"])
        self._fill_missing_reservations(scenario.get("customers", []))
        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None

    # --- dựng từ scenario -------------------------------------------------------
    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def _fixture_customer(self, c):
        return {
            "id": c["id"], "table_id": c["table_id"], "dish_id": c["dish_id"],
            "order_tick": c.get("order_tick", 0), "state": c.get("state", "waiting"),
            "patience_ticks_left": c.get("patience_ticks_left", self.patience_full),
            "eat_ticks_left": c.get("eat_ticks_left", 0), "order_status": c.get("order_status", "reserved"),
            "reserved": dict(c.get("reserved", {})), "base_price": c.get("base_price"), "tip": c.get("tip"),
        }

    def _fill_missing_reservations(self, raw):
        """Đơn reserved thiếu `reserved`: cấp theo công thức theo (order_tick, id bàn); không đủ -> unfulfillable."""
        missing = {c["id"] for c in raw if c.get("order_status", "reserved") == "reserved" and "reserved" not in c}
        todo = sorted((c for c in self.customers if c["id"] in missing),
                      key=lambda c: (c["order_tick"], id_key(c["table_id"])))
        for c in todo:
            recipe = self.menu[c["dish_id"]]["recipe"]
            if self._can_make(recipe):
                c["reserved"] = dict(recipe)
            else:
                c["order_status"] = "unfulfillable"
                c["reserved"] = {}

    # --- tiện ích kho -----------------------------------------------------------
    def _reserved_total(self) -> dict:
        tot = {}
        for c in self.customers:
            for k, n in c["reserved"].items():
                tot[k] = tot.get(k, 0) + n
        return tot

    def available(self) -> dict:
        """Kho khả dụng = tồn vật lý - phần đang giữ chỗ."""
        res = self._reserved_total()
        return {k: self.stock.get(k, 0) - res.get(k, 0) for k in sorted(set(self.stock) | set(res))}

    def _can_make(self, recipe) -> bool:
        av = self.available()
        return all(av.get(k, 0) >= n for k, n in recipe.items())

    def _clamp_rep(self, v):
        return round(max(self.t["reputation_min"], min(self.t["reputation_max"], v)), REP_DIGITS)

    # --- snapshot ---------------------------------------------------------------
    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": self.pos, "vel": self.vel},
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": [{k: c[k] for k in ("id", "table_id", "dish_id", "order_tick", "state", "patience_ticks_left",
                                             "eat_ticks_left", "order_status", "reserved", "base_price", "tip")}
                          for c in sort_by_id(self.customers)],
        }

    # --- một bước ---------------------------------------------------------------
    def step(self, inp):
        events = []
        # 1. đồng hồ, nấu, ăn, kiên nhẫn
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        ready_at_start = {s["id"] for s in self.stoves if s["state"] == "ready"}
        for s in self.stoves:
            if s["state"] == "cooking":
                s["cook_ticks_left"] = max(0, s["cook_ticks_left"] - 1)
            elif s["id"] in ready_at_start:
                s["ready_ticks"] += 1
        for c in self.customers:
            if c["state"] == "eating":
                c["eat_ticks_left"] = max(0, c["eat_ticks_left"] - 1)
            else:
                c["patience_ticks_left"] = max(0, c["patience_ticks_left"] - 1)
        # 2. bếp nấu xong -> ready
        for s in self.stoves:
            if s["state"] == "cooking" and s["cook_ticks_left"] == 0:
                s["state"], s["ready_ticks"] = "ready", 0
                events.append(("dish_ready", {"stove_id": s["id"], "order_id": s["dish"]["order_id"],
                                              "dish_id": s["dish"]["dish_id"]}))
        # 3. đi lại rồi tối đa một interact
        self._move(inp)
        if inp.pressed("interact"):
            self._interact(events)
        # 4. khách ăn xong / bỏ đi / đóng ca
        closing = self.time_left_ticks <= 0
        for c in sorted(self.customers, key=lambda c: id_key(c["table_id"])):
            if c["state"] == "eating" and (c["eat_ticks_left"] == 0 or closing):
                self._pay(c, "finished_eating" if c["eat_ticks_left"] == 0 else "closing", events)
            elif c["state"] == "waiting" and closing:
                self._leave(c, "closing", events)
            elif c["state"] == "waiting" and c["patience_ticks_left"] == 0:
                self._leave(c, "patience", events)
        if closing:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
            return events
        # 5. lượt khách mới
        if self.random_customers and self._is_customer_tick(self.phase_tick):
            self._spawn_customer(events)
        return events

    # --- interact ---------------------------------------------------------------
    def _interact(self, events):
        r = self.t["interact_radius"]
        cands = []
        for s in self.stoves:
            d = math.dist(self.pos, s["pos"])
            if d <= r:
                cands.append((d, 0, id_key(s["id"]), "stove", s))
        for tb in self.tables:
            d = math.dist(self.pos, tb["pos"])
            if d <= r:
                cands.append((d, 1, id_key(tb["id"]), "table", tb))
        if not cands:
            return
        _, _, _, kind, obj = min(cands, key=lambda c: c[:3])
        if kind == "stove":
            self._use_stove(obj, events)
        else:
            self._use_table(obj, events)

    def _use_stove(self, s, events):
        if s["state"] == "idle":
            orders = [c for c in self.customers if c["state"] == "waiting" and c["order_status"] == "reserved"]
            if not orders:
                return
            c = min(orders, key=lambda c: (c["order_tick"], id_key(c["table_id"])))
            dish = self.menu[c["dish_id"]]
            items = dict(c["reserved"])
            for k, n in items.items():
                self.stock[k] = self.stock.get(k, 0) - n
                if self.stock[k] <= 0:
                    del self.stock[k]
            c["reserved"] = {}
            c["order_status"] = "assigned"
            c["base_price"] = dish["price"]
            s["state"] = "cooking"
            s["cook_ticks_left"] = _ticks(dish["cook_s"])
            s["ready_ticks"] = 0
            s["dish"] = {"order_id": c["id"], "dish_id": c["dish_id"], "base_price": dish["price"]}
            events.append(("cook_started", {"stove_id": s["id"], "order_id": c["id"], "dish_id": c["dish_id"],
                                            "items": _expand(items), "base_price": dish["price"]}))
        elif s["state"] == "ready" and self.hand is None:
            self.hand = s["dish"]
            events.append(("dish_picked", {"stove_id": s["id"], "order_id": s["dish"]["order_id"],
                                           "dish_id": s["dish"]["dish_id"]}))
            s["state"], s["dish"], s["cook_ticks_left"], s["ready_ticks"] = "idle", None, 0, 0

    def _use_table(self, tb, events):
        if self.hand is None:
            return
        c = next((c for c in self.customers if c["table_id"] == tb["id"]), None)
        if c is None or c["state"] != "waiting" or c["id"] != self.hand["order_id"]:
            return
        base = self.hand["base_price"]
        ratio = c["patience_ticks_left"] / self.patience_full
        tip = math.floor(base * self.t["tip_rate"]) if ratio > self.t["tip_min_patience_ratio"] else 0
        c["state"], c["order_status"] = "eating", "served"
        c["eat_ticks_left"] = self.eat_full
        c["base_price"], c["tip"] = base, tip
        self.hand = None
        events.append(("served", {"order_id": c["id"], "table_id": tb["id"], "dish_id": c["dish_id"],
                                  "patience_ticks_left": c["patience_ticks_left"], "base_price": base, "tip": tip}))

    # --- khách rời bàn ------------------------------------------------------------
    def _pay(self, c, reason, events):
        amount = c["base_price"] + c["tip"]
        self.money += c["base_price"]
        self.earned += c["base_price"]
        self.shift_earned += c["base_price"]
        if c["tip"] > 0:
            self.reputation = round(self.reputation + self.t["tip_reputation"], REP_DIGITS)
        events.append(("paid", {"order_id": c["id"], "table_id": c["table_id"], "base_price": c["base_price"],
                                "tip": c["tip"], "amount": amount, "reason": reason}))
        self.customers.remove(c)

    def _leave(self, c, reason, events):
        # bỏ món của đơn đang nấu / ready / trên tay; phần giữ thô được nhả khi khách rời
        for s in self.stoves:
            if s["dish"] and s["dish"]["order_id"] == c["id"]:
                s["state"], s["dish"], s["cook_ticks_left"], s["ready_ticks"] = "idle", None, 0, 0
        if self.hand and self.hand["order_id"] == c["id"]:
            self.hand = None
        events.append(("customer_left", {"order_id": c["id"], "table_id": c["table_id"], "reason": reason,
                                         "reputation": self.reputation}))
        self.reputation = self._clamp_rep(self.reputation + self.t["left_reputation_delta"])
        self.customers.remove(c)

    # --- khách mới ----------------------------------------------------------------
    def _is_customer_tick(self, pt) -> bool:
        first = self.t["first_customer_tick"]
        interval = _ticks(self.t["customer_interval_s"])
        return pt > first and (pt - first) % interval == 0

    def _spawn_customer(self, events):
        busy = {c["table_id"] for c in self.customers}
        free = [tb for tb in self.tables if tb["id"] not in busy]
        if not free:
            return
        table = min(free, key=lambda tb: id_key(tb["id"]))
        options = [d for d in sorted(self.menu) if self._can_make(self.menu[d]["recipe"])]
        if not options:
            events.append(("no_dish", {}))
            return
        dish_id = self.rng.get("customers").choice(options)
        cid = self.ids.new("C")
        self.customers.append({
            "id": cid, "table_id": table["id"], "dish_id": dish_id, "order_tick": self.phase_tick,
            "state": "waiting", "patience_ticks_left": self.patience_full, "eat_ticks_left": 0,
            "order_status": "reserved", "reserved": dict(self.menu[dish_id]["recipe"]),
            "base_price": None, "tip": None,
        })
        events.append(("customer_arrived", {"order_id": cid, "table_id": table["id"], "dish_id": dish_id}))

    # --- di chuyển ----------------------------------------------------------------
    def _move(self, inp):
        speed = self.t["walk_speed"]
        mx, mz = inp.move
        self.vel = ramp_velocity(self, (mx * speed, mz * speed), int(self.t.get("ramp_max_ticks", 6)))
        b = self.t["bounds"]
        for i, axis in enumerate(("x", "z")):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])
