"""Vòng tick (Contract B, mô hình tick) — v1.1: pause, mode day, ba bộ đếm tick.

Thứ tự ghi: (event tick 0 của mode day) -> snapshot tick 0 -> với mỗi bước: sự kiện (theo thứ tự xử lý) rồi
snapshot (nếu tới lượt hoặc buổi kết thúc) -> dòng 'end'. Mỗi tick tối đa một snapshot.

  tick       : số bước ngoài (kể cả bước đang pause)
  sim_tick   : số bước gameplay toàn lượt (đứng yên khi pause)
  phase_tick : số bước gameplay trong pha hiện tại (về 0 khi đổi pha)

Pause (Ticket-02 mục 4.2): xét cạnh `pause` trước. Bước vào pause chỉ tăng tick ngoài và phát `paused`; khi còn
pause bỏ qua mọi hành động; cạnh lên tiếp theo phát `resumed` rồi chạy gameplay ngay trong bước đó.

`Session` là API bước tick dùng chung cho headless (`run`) và cửa sổ chơi trực tiếp (`chonoi.live`).
"""

import math

from .ids import IdAllocator
from .inputs import InputPlayer
from .inventory import write_inventory
from .jsonl import dumps
from .rng import Streams
from .sim.day import DaySim
from .sim.gather import GatherSim
from .sim.quan import QuanSim


def build_sim(mode, tuning, scenario, seed, inventory, days=1):
    streams, ids = Streams(seed), IdAllocator()
    if mode == "gather":
        return GatherSim(tuning, scenario, streams, ids)
    if mode == "day":
        return DaySim(tuning, scenario, streams, ids, days=days)
    return QuanSim(tuning, scenario, streams, ids, inventory=inventory)


class Session:
    """Một lượt chơi: dựng sim, bước từng tick, lấy snapshot / dòng end."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None, days=1):
        self.mode = mode
        self.tuning = tuning
        self.sim = build_sim(mode, tuning, scenario, seed, inventory, days)
        self.tick = 0
        self.sim_tick = 0
        self.paused = False

    @property
    def done(self) -> bool:
        return self.sim.done

    def _state(self):
        if self.sim.done:
            return "finished"
        return "paused" if self.paused else "playing"

    def _score(self):
        return self.sim.earned + self.tuning["score"]["reputation_multiplier"] * math.floor(self.sim.reputation)

    def _event(self, name, data, phase=None):
        row = {"type": "event", "tick": self.tick, "phase": phase or self.sim.phase}
        if self.mode == "day":
            row["day"] = self.sim.day
        row.update({"name": name, "data": data})
        return row

    def _rows(self, events):
        return [self._event(*e) for e in events]

    def initial_events(self) -> list:
        """Event tick 0 (mode day: day_start, day_plan, phase_start(gather)); ghi trước snapshot tick 0."""
        return self._rows(getattr(self.sim, "initial_events", []))

    def snapshot(self) -> dict:
        sim = self.sim
        s = {"type": "snapshot", "tick": self.tick, "sim_tick": self.sim_tick, "mode": self.mode, "phase": sim.phase,
             "phase_tick": sim.phase_tick, "state": self._state(), "time_left_ticks": sim.time_left_ticks,
             "money": sim.money, "earned": sim.earned, "reputation": sim.reputation, "score": self._score()}
        s.update(sim.snapshot())
        return s

    def step(self, inp) -> list:
        """Chạy một bước ngoài với `inp` (chonoi.inputs.InputState); trả các dòng event (tick = k + 1)."""
        self.tick += 1
        rows = []
        if inp.pressed("pause"):
            self.paused = not self.paused
            rows.append(self._event("paused" if self.paused else "resumed", {}))
        if self.paused:  # bước vào pause và các bước còn pause: chỉ tăng tick ngoài
            return rows
        # bước resumed rơi xuống đây: chạy gameplay ngay trong bước đó (Ticket-02 4.2)
        self.sim_tick += 1
        return rows + self._rows(self.sim.step(inp))

    def end_row(self) -> dict:
        sim = self.sim
        row = {"type": "end", "ticks": self.tick, "sim_tick": self.sim_tick, "mode": self.mode,
               "state": self._state(), "reason": sim.reason if sim.done else "tick_limit",
               "money": sim.money, "earned": sim.earned, "reputation": sim.reputation, "score": self._score()}
        if self.mode == "day":
            row["days_completed"] = sim.days_completed
        return row

    def write_inventory_if_done(self, inventory_out):
        """File kho: ghi MỘT lần khi có gather_end; chưa kết thúc thì giữ nguyên file đích."""
        if self.mode == "gather" and self.sim.done and inventory_out:
            write_inventory(inventory_out, self.sim.inventory_items())


def run(mode, tuning, scenario, seed, frames, ticks, out_path, snapshot_every, inventory=None, inventory_out=None,
        days=1):
    """Chạy hết rồi mới ghi file: lỗi fixture phát hiện giữa lượt (mode day, lúc mở quán) vẫn thoát mã 2
    trước khi có đầu ra."""
    sess = Session(mode, tuning, scenario, seed, inventory, days)
    player = InputPlayer(frames)
    lines = [dumps(r) for r in sess.initial_events()]
    lines.append(dumps(sess.snapshot()))  # tick 0: sau khi dựng scenario, trước mọi input
    last_snapped = 0
    while sess.tick < ticks and not sess.done:
        inp = player.advance(sess.tick)  # bước k đọc input có tick == k
        lines.extend(dumps(r) for r in sess.step(inp))
        if sess.tick % snapshot_every == 0 or sess.done:
            lines.append(dumps(sess.snapshot()))
            last_snapped = sess.tick
    if last_snapped != sess.tick:
        lines.append(dumps(sess.snapshot()))
    lines.append(dumps(sess.end_row()))
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    sess.write_inventory_if_done(inventory_out)
    return sess.sim
