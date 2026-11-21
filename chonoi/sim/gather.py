"""Buổi sáng — Lặn & Hái (`gather`). KHUNG: bơi, chặn mép, đồng hồ, cập bến, xuất kho.

Mặt cắt dòng sông nhìn NGANG: vị trí `[x, d]` (x sang phải, `d` độ sâu hướng xuống, d = 0 là mặt nước).
`move = [x, d]`: thành phần thứ hai DƯƠNG = bơi xuống. Hướng mặt là góc từ +x, dương = xuống.

Đã làm sẵn để smoke test chạy được: bơi + tăng/giảm tốc, chặn mép (d không âm), đồng hồ và hết giờ,
cập bến (`interact` trong vùng bến -> `gather_end` reason `docked`), xuất kho, snapshot đầy đủ trường gather.

Lát 1 (bơi + oxy + biên + giỏ) — PRD-0 mục F "Gather":
      - oxy: dưới nước (d > surface_depth) trừ 1 tick/tick, mặt nước hồi oxygen_refill_per_tick, kẹp [0, max]
      - ngạt: oxy = 0 và đang dưới nước -> đếm zero_oxy_ticks, đủ choke_interval_ticks thì -1 Máu (choke)
      - Máu về 0 -> ngất (faint, gather_end reason `fainted`, mất toàn bộ giỏ, kho rỗng)
      - sự kiện dive / surface / oxygen_empty / choke / faint
      - giỏ: thứ tự nhặt (LIFO), sức chứa hold_capacity
Lát 2 (hái + bắt cá + cập bến + kho):
      - hái nút ở mặt nước (gather, hold_full), nút mọc lại (node_regrown đã có phần đếm ngược)
      - bắt đàn cá bằng `catch` (fish_caught, hold_full, hồi chiêu catch_cd_ticks, chỉ khi dưới nước)
      - cập bến xét TRƯỚC hái (đã có); ghi kho đúng một lần do runner lo
Phase 2 (contract v1.1, Ticket-02 mục 1.1–1.2, thứ tự mục 4.5):
      - đàn cá bơi / sinh theo lịch (`sim/fish.py`), fish_initial là số đàn đầu ca
      - Cá Sấu tuần tra / đuổi / chạm / lùi (`sim/monsters.py`): monster_hit, bất tử, rơi hàng LIFO, faint "monster"
      - Máu và oxy tối đa theo cấp nâng cấp đang áp dụng (mode day truyền vào)
"""

import math

from ..ids import id_key, sort_by_id
from ..inventory import hold_to_items
from . import fish as fishmod
from . import monsters as monmod
from .ramp import ramp_velocity

TICK = 60.0
AXES = ("x", "d")


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids, day=1, hp_max=None, oxygen_max_s=None):
        t = tuning["gather"]
        self.t = t
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        self.heading = float(p.get("heading_deg", t["start_heading_deg"]))
        self.oxygen_max = int(round((oxygen_max_s if oxygen_max_s is not None else t["oxygen_max_s"]) * TICK))
        self.oxygen_ticks = p.get("oxygen_ticks", self.oxygen_max)
        self.hp_max = hp_max if hp_max is not None else t["hp_max"]
        self.hp = p.get("hp", self.hp_max)
        self.zero_oxy_ticks = p.get("zero_oxy_ticks", 0)
        self.invuln_ticks = p.get("invuln_ticks", 0)
        self.catch_cd_ticks = p.get("catch_cd_ticks", 0)
        self.hold = list(scenario.get("hold", []))  # thứ tự nhặt, cuối mảng là mới nhất
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        # nút và đàn cá: scenario THAY THẾ danh sách mặc định; random_fish=false tắt cá mặc định
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]
        # random_fish=false: tắt cá mặc định, bơi và sinh (cá fixture đứng yên). Khai fish khi cờ bật: thay đàn
        # ban đầu, vẫn bơi / sinh.
        self.fish_active = scenario.get("random_fish", True)
        src_fish = scenario.get("fish", [])
        self.fish = [{"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                      "heading_deg": float(f.get("heading_deg", 0)), "age_ticks": f.get("age_ticks", 0)}
                     for f in src_fish]
        self.monsters = monmod.build(t, scenario, day)
        for coll in (self.nodes, self.fish, self.monsters):
            for e in coll:
                ids.reserve(e["id"])
        if "fish" not in scenario and self.fish_active:
            self.fish = fishmod.initial_fish(t, streams, ids)
        self.phase_tick = 0
        self.money = 0
        self.earned = 0
        self.reputation = tuning["quan"]["reputation_initial"]
        self.done = False
        self.reason = None

    # --- giao diện cho runner -------------------------------------------------
    def inventory_items(self) -> dict:
        return hold_to_items(self.hold)

    def snapshot(self) -> dict:
        return {
            "player": {"pos": self.pos, "vel": self.vel, "heading_deg": self.heading,
                       "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                       "hp": self.hp, "hp_max": self.hp_max, "zero_oxy_ticks": self.zero_oxy_ticks,
                       "invuln_ticks": self.invuln_ticks, "catch_cd_ticks": self.catch_cd_ticks,
                       "at_surface": self._at_surface()},
            "hold": self.hold, "hold_count": len(self.hold),
            "hold_capacity": self.t["hold_capacity"],
            "nodes": [{"id": n["id"], "pos": n["pos"], "kind": n["kind"],
                       "ready": n["regrow_ticks"] == 0, "regrow_ticks": n["regrow_ticks"]}
                      for n in sort_by_id(self.nodes)],
            "fish": [{"id": f["id"], "pos": f["pos"], "kind": f["kind"], "heading_deg": f["heading_deg"],
                      "age_ticks": f["age_ticks"]} for f in sort_by_id(self.fish)],
            "monsters": monmod.snapshot(self.monsters),
        }

    # --- một bước ---------------------------------------------------------------
    def step(self, inp):
        events = []
        # 1. đồng hồ và hàng có sẵn: giảm bộ đếm, nút mọc lại
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    events.append(("node_regrown", {"node_id": n["id"]}))
        # 2. bơi + chặn mép, so phân vùng đầu/cuối bước -> dive / surface
        was_surface = self._at_surface()
        self._move(inp)
        now_surface = self._at_surface()
        if was_surface and not now_surface:
            events.append(("dive", {"pos": list(self.pos)}))
        elif now_surface and not was_surface:
            events.append(("surface", {"pos": list(self.pos)}))
        # oxy theo d CUỐI bước, ngạt, Máu, ngất
        if self._oxygen(events):
            return events
        # 2b. thủy quái theo id rồi tối đa một hit
        just_free = monmod.update(self.t, self.monsters, self.pos)
        hit = monmod.find_hit(self.t, self.monsters, self.pos, self.invuln_ticks, just_free)
        if hit is not None and self._monster_hit(hit, events):
            return events
        # 3. interact: bến trước, rồi hái
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            if self._at_surface():
                self._harvest(events)
        # 4. bắt cá
        if inp.pressed("catch") and self.catch_cd_ticks == 0 and not self._at_surface():
            self._catch(events)
        # 5. hết giờ
        if self.time_left_ticks <= 0:
            self._finish("time", events)
            return events
        # 6. còn giờ: cá bơi rồi sinh theo lịch (cá mới tham gia từ bước sau)
        if self.fish_active:
            fishmod.swim(self.t, self.fish, self.rng)
            ev = fishmod.maybe_spawn(self.t, self.fish, self.rng, self.ids, self.phase_tick)
            if ev:
                events.append(ev)
        return events

    # --- tiện ích ---------------------------------------------------------------
    def _at_surface(self) -> bool:
        return self.pos[1] <= self.t["surface_depth"]

    def _oxygen(self, events) -> bool:
        """Cập nhật oxy / ngạt / Máu sau khi bơi. Trả True nếu vừa ngất (buổi sáng kết thúc)."""
        if self._at_surface():
            self.oxygen_ticks = min(self.oxygen_max, self.oxygen_ticks + self.t["oxygen_refill_per_tick"])
            self.zero_oxy_ticks = 0  # mặt nước: hồi oxy và reset ngạt
            return False
        prev = self.oxygen_ticks
        self.oxygen_ticks = max(0, self.oxygen_ticks - 1)
        if prev > 0 and self.oxygen_ticks == 0:
            events.append(("oxygen_empty", {"oxygen_ticks": 0}))
        if self.oxygen_ticks == 0:  # kể cả bước vừa chạm 0
            self.zero_oxy_ticks += 1
            if self.zero_oxy_ticks >= self.t["choke_interval_ticks"]:
                self.zero_oxy_ticks = 0
                events.append(("choke", {"hp": self.hp}))
                self.hp -= 1
                if self.hp <= 0:
                    self.hp = 0
                    lost = self.hold[::-1]  # LIFO: nhặt sau bỏ trước
                    self.hold = []  # ngất: mất toàn bộ giỏ, gather_end và file kho đều rỗng
                    events.append(("faint", {"cause": "choke", "lost": lost, "hp": 0}))
                    self._finish("fainted", events)
                    return True
        return False

    def _monster_hit(self, m, events) -> bool:
        """Chạm thủy quái: -1 Máu, rơi hàng LIFO theo loss_ratio, bất tử, quái lùi. Trả True nếu ngất."""
        mt = self.t["monsters"]
        n = int(len(self.hold) * mt["loss_ratio"] + 0.5)
        lost = [self.hold.pop() for _ in range(n)]
        self.hp -= 1
        self.invuln_ticks = mt["invuln_ticks"]
        monmod.start_recoil(self.t, m, self.pos)
        events.append(("monster_hit", {"monster_id": m["id"], "hp": max(0, self.hp), "lost": lost,
                                       "pos": list(self.pos)}))
        if self.hp > 0:
            return False
        self.hp = 0
        rest = list(reversed(self.hold))
        self.hold = []
        events.append(("faint", {"cause": "monster", "lost": rest, "hp": 0}))
        self._finish("fainted", events)
        return True

    def _free(self) -> int:
        return self.t["hold_capacity"] - len(self.hold)

    @staticmethod
    def _nearest(cands):
        """cands: [(khoảng cách, id, thực thể)] -> thực thể gần nhất, hòa theo id."""
        if not cands:
            return None
        return min(cands, key=lambda c: (c[0], id_key(c[1])))[2]

    def _harvest(self, events):
        """Hái nút `ready` gần nhất trong interact_radius (id nhỏ khi bằng nhau)."""
        r = self.t["interact_radius"]
        cands = [(math.dist(self.pos, n["pos"]), n["id"], n) for n in self.nodes
                 if n["regrow_ticks"] == 0 and math.dist(self.pos, n["pos"]) <= r]
        node = self._nearest(cands)
        if node is None:
            return
        amount = self.t["node_yield"]
        if self._free() < amount:
            events.append(("hold_full", {"action": "gather", "node_id": node["id"],
                                         "required": amount, "free": self._free()}))
            return
        self.hold.extend([node["kind"]] * amount)
        node["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))
        events.append(("gather", {"node_id": node["id"], "kind": node["kind"], "amount": amount}))

    def _catch(self, events):
        """Bắt đàn cá gần nhất trong catch_radius (id nhỏ khi bằng nhau), lấy đủ yield hoặc hold_full."""
        r = self.t["catch_radius"]
        cands = sorted(((math.dist(self.pos, f["pos"]), f["id"], f) for f in self.fish
                        if math.dist(self.pos, f["pos"]) <= r), key=lambda c: (c[0], id_key(c[1])))
        if not cands:
            return
        cd = int(round(self.t["catch_cooldown_s"] * TICK))
        for _, _, fish in cands:
            y = self.t["fish_yield"][fish["kind"]]
            if self._free() >= y:
                self.hold.extend([fish["kind"]] * y)
                self.fish.remove(fish)
                self.catch_cd_ticks = cd
                events.append(("fish_caught", {"fish_id": fish["id"], "kind": fish["kind"], "yield": y}))
                return
        fish = cands[0][2]
        events.append(("hold_full", {"action": "catch", "node_id": fish["id"],
                                     "required": self.t["fish_yield"][fish["kind"]], "free": self._free()}))
        self.catch_cd_ticks = cd

    def _in_dock(self) -> bool:
        return math.dist(self.pos, self.t["dock_pos"]) <= self.t["dock_radius"]

    def _finish(self, reason, events):
        self.done = True
        self.reason = reason
        events.append(("gather_end", {"reason": reason, "inventory": {"items": self.inventory_items()}}))

    def _move(self, inp):
        speed = self.t["swim_speed"]
        mx, md = inp.move
        self.vel = ramp_velocity(self, (mx * speed, md * speed), int(self.t["ramp_max_ticks"]))
        if (mx, md) != (0.0, 0.0):
            self.heading = math.degrees(math.atan2(md, mx)) % 360
        b = self.t["bounds"]
        for i, axis in enumerate(AXES):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i] = lo
                self.vel[i] = max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i] = hi
                self.vel[i] = min(0.0, self.vel[i])
