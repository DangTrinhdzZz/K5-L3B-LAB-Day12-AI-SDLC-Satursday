"""Vòng ngày (`--mode day`) — Ticket-02 mục 2 và 4.5 "Đổi pha" / "Shop".

Mỗi Ngày: day_start -> day_plan -> phase_start(gather) -> ... gather_end -> phase_start(quan) -> ... quan_end
-> phase_start(shop) -> ... shop_end -> (Ngày kế, hoặc kết thúc `days_complete` sau --days Ngày).
Pha mới dựng ngay trong tick đổi pha và chỉ chạy gameplay từ bước sau.

Xuyên Ngày: money, earned, reputation, cấp đã mua (`upgrades`). Chỉ khi dựng Ngày mới mới sao cấp đã mua sang
`active_upgrades` (Máu / oxy tối đa của buổi sáng). Giỏ làm mới, kho dư bị bỏ sau Shop.
DayIntro / EveningIntro / DayResult / Summary chỉ là màn hình của cửa sổ chơi, không phải pha headless.
v1.2: bàn giao kho CÁ THỂ trong bộ nhớ ngay tick đổi pha (không hao thêm); hàng ở Shop không hao; Ngày đầu giữ
nguyên id của mẫu gather.hold, các Ngày kế cấp id mới theo thứ tự mảng với kind / fresh ban đầu.

step() trả danh sách (name, data, phase): event kết thúc mang pha cũ, event mở pha mang pha mới.
"""

from ..contract import validate_plan_entry
from ..freshness import item_out
from ..ids import id_key, sort_by_id
from .gather import GatherSim
from .quan import QuanSim

UPGRADE_FIELD = {"oxygen": "oxygen_max_s", "hp": "hp_max"}


class ShopSim:
    phase = "shop"

    def __init__(self, tuning, stock):
        self.time_left_ticks = tuning["shop"]["max_ticks"]
        self.stock = sort_by_id(stock)  # cá thể dư từ ca quán, không hao trong Shop
        self.phase_tick = 0
        self.done = False
        self.reason = None

    def snapshot(self) -> dict:
        return {"stock": [item_out(it) for it in self.stock]}


class DaySim:
    mode = "day"

    def __init__(self, tuning, scenario, streams, ids, days=1):
        self.t = tuning
        self.streams = streams
        self.ids = ids
        self.days = days
        self.tpl_gather = scenario.get("gather", {})
        self.tpl_quan = scenario.get("quan", {})
        d = scenario.get("day", {})
        self.money = d.get("money", 0)
        self.earned = d.get("earned", 0)
        self.reputation = float(d.get("reputation", tuning["quan"]["reputation_initial"]))
        self.upgrades = {k: v for k, v in d.get("upgrades", {}).items() if v > 0}
        self.active_upgrades = {}
        self.plans = {e["day"]: {"dishes": dict(e["dishes"]), "ingredients": dict(e["ingredients"])}
                      for e in tuning["day_plan"]}
        for e in d.get("day_plan", []):
            self.plans[e["day"]] = {"dishes": dict(e["dishes"]),
                                    "ingredients": validate_plan_entry(f"day.day_plan[{e['day']}]", e, tuning["menu"])}
        self.day = 0
        self.days_completed = 0
        self.sub = None
        self.done = False
        self.reason = None
        self.initial_events = self._start_day(1)

    # --- thuộc tính chung cho runner ---------------------------------------------
    @property
    def phase(self):
        return self.sub.phase

    @property
    def phase_tick(self):
        return self.sub.phase_tick

    @property
    def time_left_ticks(self):
        return self.sub.time_left_ticks

    def _live(self, name):
        """Tiền / earned / uy tín: trong ca quán đọc từ QuanSim, còn lại từ trạng thái xuyên Ngày."""
        if isinstance(self.sub, QuanSim):
            return getattr(self.sub, name)
        return getattr(self, "_" + name)

    money = property(lambda s: s._live("money"), lambda s, v: setattr(s, "_money", v))
    earned = property(lambda s: s._live("earned"), lambda s, v: setattr(s, "_earned", v))
    reputation = property(lambda s: s._live("reputation"), lambda s, v: setattr(s, "_reputation", v))

    def plan(self):
        """Kế hoạch của Ngày hiện tại; quá 5 Ngày (soak) thì D1–D5 lặp lại."""
        return self.plans[(self.day - 1) % len(self.plans) + 1]

    def snapshot(self) -> dict:
        s = self.sub.snapshot()
        s.update({"day": self.day, "day_plan": {"dishes": dict(self.plan()["dishes"]),
                                                "ingredients": dict(self.plan()["ingredients"])},
                  "upgrades": dict(self.upgrades), "active_upgrades": dict(self.active_upgrades)})
        return s

    # --- dựng pha ------------------------------------------------------------------
    def _level_value(self, up, base):
        lv = self.active_upgrades.get(up, 0)
        if lv <= 0:
            return base
        return self.t["shop"]["upgrades"][up][lv - 1][UPGRADE_FIELD[up]]

    def _start_day(self, n):
        self.day = n
        self.active_upgrades = dict(self.upgrades)
        g = self.t["gather"]
        self.sub = GatherSim(self.t, self.tpl_gather, self.streams, self.ids, day=n,
                             hp_max=self._level_value("hp", g["hp_max"]),
                             oxygen_max_s=self._level_value("oxygen", g["oxygen_max_s"]), new_hold_ids=n > 1)
        plan = self.plan()
        return [("day_start", {}, "gather"),
                ("day_plan", {"dishes": dict(plan["dishes"]), "ingredients": dict(plan["ingredients"])}, "gather"),
                ("phase_start", {}, "gather")]

    def _open_quan(self):
        stock = self.sub.inventory_items()
        self.sub = QuanSim(self.t, self.tpl_quan, self.streams, self.ids, inventory=stock,
                           plan_dishes=sorted(self.plan()["dishes"], key=id_key), money=self._money,
                           earned=self._earned, reputation=self._reputation)
        return [("phase_start", {}, "quan")]

    def _open_shop(self):
        q = self.sub
        self._money, self._earned, self._reputation = q.money, q.earned, q.reputation
        self.sub = ShopSim(self.t, q.stock)
        return [("phase_start", {}, "shop")]

    def _close_shop(self, reason):
        out = [("shop_end", {"reason": reason}, "shop", self.day)]  # event kết thúc mang Ngày cũ
        self.days_completed += 1
        if self.day >= self.days:
            self.sub.done = True
            self.done = True
            self.reason = "days_complete"
            return out
        return out + self._start_day(self.day + 1)

    # --- Shop ------------------------------------------------------------------------
    def _buy(self, cmd):
        levels = self.t["shop"]["upgrades"].get(cmd) if cmd in UPGRADE_FIELD else None
        if levels is None:
            return ("buy_failed", {"action": cmd, "reason": "unknown"}, "shop")
        nxt = self.upgrades.get(cmd, 0) + 1
        if nxt > len(levels):
            return ("buy_failed", {"action": cmd, "reason": "max_level"}, "shop")
        price = levels[nxt - 1]["price"]
        if self._money < price:
            return ("buy_failed", {"action": cmd, "reason": "funds"}, "shop")
        self._money -= price
        self.upgrades[cmd] = nxt
        return ("bought", {"upgrade": cmd, "level": nxt, "price": price, "money": self._money}, "shop")

    def _step_shop(self, inp):
        shop = self.sub
        shop.phase_tick += 1
        shop.time_left_ticks = max(0, shop.time_left_ticks - 1)
        out = []
        if inp.buy is not None:
            out.append(self._buy(inp.buy))
        if inp.pressed("shop_done"):
            return out + self._close_shop("done")
        if shop.time_left_ticks <= 0:
            return out + self._close_shop("time")
        return out

    # --- một bước gameplay ------------------------------------------------------------
    def step(self, inp):
        if self.done:
            return []
        phase = self.sub.phase
        if phase == "shop":
            return self._step_shop(inp)
        out = [(name, data, phase) for name, data in self.sub.step(inp)]
        if self.sub.done:
            out += self._open_quan() if phase == "gather" else self._open_shop()
        return out
