"""Bot tất định cho soak headless (Ticket-04 mục 2). Chỉ đọc trạng thái sim, không dùng ngẫu nhiên hay đồng hồ:
cùng seed -> cùng chuỗi input -> cùng kết quả.

Chiến lược đơn giản, đủ để mỗi Ngày đi qua gather -> quan -> shop và có thu nhập:
  gather: hái nút / bắt cá thuộc nguyên liệu kế hoạch còn thiếu, nổi lên khi oxy thấp, tránh Cá Sấu, về bến khi đủ
          hàng / gần hết giờ / giỏ đầy.
  quan  : bưng món chín -> phục vụ đúng bàn; bếp rảnh thì nấu đơn đang giữ chỗ.
  shop  : mua nâng cấp kế tiếp nếu đủ tiền (oxy trước, rồi Máu), rồi đóng Shop.
"""

import math

from .inputs import InputState
from .inventory import kind_counts
from .sim.gather import GatherSim
from .sim.quan import QuanSim

IDLE = InputState((0.0, 0.0), {}, set())


def _toward(pos, target, stop=0.2):
    dx, dy = target[0] - pos[0], target[1] - pos[1]
    n = math.hypot(dx, dy)
    if n <= stop:
        return (0.0, 0.0)
    return (dx / n, dy / n)


def _act(move, *buttons, buy=None):
    return InputState(move, {}, set(buttons), buy)


class Bot:
    def __init__(self, tuning):
        self.t = tuning
        self.shop_done_next = False

    def decide(self, day_sim) -> InputState:
        sub = day_sim.sub
        if isinstance(sub, GatherSim):
            return self._gather(day_sim, sub)
        if isinstance(sub, QuanSim):
            return self._quan(sub)
        return self._shop(day_sim)

    # --- buổi sáng -------------------------------------------------------------------
    def _gather(self, day_sim, g):
        t = g.t
        pos = g.pos
        dock = t["dock_pos"]
        need = dict(day_sim.plan()["ingredients"])
        have = kind_counts([it for it in g.hold if not g.fresh.is_spoiled(it)])
        missing = {k: n - have.get(k, 0) for k, n in need.items() if n - have.get(k, 0) > 0}
        dist_dock = math.dist(pos, dock)
        # về bến: đủ hàng, giỏ đầy, hoặc sắp hết giờ (thời gian bơi về + 5 s dự phòng)
        if not missing or len(g.hold) >= t["hold_capacity"] or g.time_left_ticks < (dist_dock / t["swim_speed"] + 5) * 60:
            if dist_dock <= t["dock_radius"] * 0.8:
                return _act((0.0, 0.0), "interact")
            return _act(_toward(pos, dock))
        under = not g._at_surface()
        # nổi lên khi oxy thấp hoặc Cá Sấu ở gần
        oxy_need = (pos[1] / t["swim_speed"] + 3) * 60
        danger = any(math.dist(m["pos"], pos) < 8 for m in g.monsters) and pos[1] >= 8
        if under and (g.oxygen_ticks < oxy_need or danger):
            return _act((0.0, -1.0))
        # mục tiêu: nút sẵn sàng của loại còn thiếu, hoặc đàn cá còn thiếu xa Cá Sấu
        cands = []
        for n in g.nodes:
            if n["regrow_ticks"] == 0 and n["kind"] in missing:
                cands.append((math.dist(pos, n["pos"]), "node", n))
        if g.oxygen_ticks > g.oxygen_max * 0.5:
            for f in g.fish:
                if f["kind"] in missing and t["fish_yield"][f["kind"]] <= t["hold_capacity"] - len(g.hold) \
                        and all(math.dist(m["pos"], f["pos"]) > 10 for m in g.monsters):
                    cands.append((math.dist(pos, f["pos"]), "fish", f))
        if not cands:
            if dist_dock <= t["dock_radius"] * 0.8:
                return _act((0.0, 0.0), "interact")
            return _act(_toward(pos, dock))
        cands.sort(key=lambda c: (c[0], c[1], c[2]["id"]))
        _, kind, target = cands[0]
        if kind == "node":
            if under:
                return _act(_toward(pos, [target["pos"][0], 0.0]))
            if math.dist(pos, target["pos"]) <= t["interact_radius"] * 0.9:
                return _act((0.0, 0.0), "interact")
            return _act(_toward(pos, target["pos"]))
        if math.dist(pos, target["pos"]) <= t["catch_radius"] * 0.8 and g.catch_cd_ticks == 0 and under:
            return _act(_toward(pos, target["pos"]), "catch")
        return _act(_toward(pos, target["pos"]))

    # --- buổi tối --------------------------------------------------------------------
    def _quan(self, q):
        pos, r = q.pos, q.t["interact_radius"] * 0.6
        if q.hand is not None:
            c = next((c for c in q.customers if c["id"] == q.hand["order_id"]), None)
            if c is None:
                return IDLE
            tb = next(tb for tb in q.tables if tb["id"] == c["table_id"])
            return self._go_use(pos, tb["pos"], r)
        ready = [s for s in q.stoves if s["state"] == "ready"]
        if ready:
            s = min(ready, key=lambda s: math.dist(pos, s["pos"]))
            return self._go_use(pos, s["pos"], r)
        waiting = any(c["state"] == "waiting" and c["order_status"] == "reserved" for c in q.customers)
        idle = [s for s in q.stoves if s["state"] == "idle"]
        if waiting and idle:
            s = min(idle, key=lambda s: math.dist(pos, s["pos"]))
            return self._go_use(pos, s["pos"], r)
        return _act(_toward(pos, [5.0, 6.0]))

    @staticmethod
    def _go_use(pos, target, r):
        if math.dist(pos, target) <= r:
            return _act((0.0, 0.0), "interact")
        return _act(_toward(pos, target))

    # --- Shop -------------------------------------------------------------------------
    def _shop(self, day_sim):
        if self.shop_done_next:
            self.shop_done_next = False
            return _act((0.0, 0.0), "shop_done")
        self.shop_done_next = True
        ups = self.t["shop"]["upgrades"]
        for up in ("oxygen", "hp"):
            lv = day_sim.upgrades.get(up, 0)
            if lv < len(ups[up]) and day_sim.money >= ups[up][lv]["price"]:
                return _act((0.0, 0.0), buy=up)
        return IDLE
