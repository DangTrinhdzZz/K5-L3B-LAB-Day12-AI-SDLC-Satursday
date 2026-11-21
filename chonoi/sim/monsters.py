"""Thủy quái (Cá Sấu Năm Chèo) — Ticket-02 mục 1.2, contract v1.1.

Mỗi con: {id, kind, pos, waypoints [w0, w1], target_idx, state (patrol/chase/recoil), state_ticks_left, recoil_dir}.
  patrol: đi patrol_speed tới waypoints[target_idx]; đến nơi thì đổi mục tiêu cho bước sau.
  chase : người chơi ở d ≥ ngưỡng độ sâu của loài (depths[0]) và cách ≤ detect_radius -> bơi về phía người chơi
          ở chase_speed; về patrol khi cách > exit_radius hoặc người chơi lên d < ngưỡng.
  recoil: sau khi gây hit, recoil_ticks bước tính từ bước sau, lùi recoil_dist/recoil_ticks mỗi bước theo hướng
          xa người chơi đã chốt lúc chạm; không gây hit; hết recoil về patrol, xét phát hiện/chạm từ bước kế.
Vị trí luôn chặn theo biên x của map và dải độ sâu của loài.
"""

import math

from ..ids import id_key, sort_by_id

TICK = 60.0
STATES = ("patrol", "chase", "recoil")


def build(t, scenario, day):
    """Danh sách quái đầu ca: scenario.monsters thay thế bố trí mặc định của đúng Ngày."""
    if "monsters" in scenario:
        src = scenario["monsters"]
    else:
        src = [s for s in t["monsters"]["spawns"] if s["from_day"] <= day]
    out = []
    for m in src:
        wps = [[float(c) for c in w] for w in m["waypoints"]]
        out.append({"id": m["id"], "kind": m["kind"], "pos": [float(c) for c in m.get("pos", wps[0])],
                    "waypoints": wps, "target_idx": m.get("target_idx", 1), "state": m.get("state", "patrol"),
                    "state_ticks_left": m.get("state_ticks_left", 0),
                    "recoil_dir": list(m["recoil_dir"]) if m.get("recoil_dir") is not None else None})
    return out


def snapshot(monsters):
    return [{k: m[k] for k in ("id", "kind", "pos", "waypoints", "target_idx", "state", "state_ticks_left",
                                "recoil_dir")} for m in sort_by_id(monsters)]


def _clamp(t, sp, pos):
    xlo, xhi = t["bounds"]["x"]
    dlo, dhi = sp["depths"]
    return [min(max(pos[0], xlo), xhi), min(max(pos[1], dlo), dhi)]


def _toward(pos, target, step):
    dist = math.dist(pos, target)
    if dist <= step:
        return [target[0], target[1]], True
    return [pos[0] + (target[0] - pos[0]) / dist * step, pos[1] + (target[1] - pos[1]) / dist * step], False


def update(t, monsters, player_pos):
    """Cập nhật mọi con theo id. Trả tập id vừa hết recoil (không xét chạm ở bước này)."""
    species = t["monsters"]["species"]
    just_free = set()
    for m in sort_by_id(monsters):
        sp = species[m["kind"]]
        if m["state"] == "recoil":
            step = sp["recoil_dist"] / sp["recoil_ticks"]
            m["pos"] = _clamp(t, sp, [m["pos"][0] + m["recoil_dir"][0] * step, m["pos"][1] + m["recoil_dir"][1] * step])
            m["state_ticks_left"] -= 1
            if m["state_ticks_left"] <= 0:
                m["state"], m["state_ticks_left"], m["recoil_dir"] = "patrol", 0, None
                just_free.add(m["id"])
            continue
        thr = sp["depths"][0]
        dist = math.dist(m["pos"], player_pos)
        if m["state"] == "patrol" and player_pos[1] >= thr and dist <= sp["detect_radius"]:
            m["state"] = "chase"
        elif m["state"] == "chase" and (dist > sp["exit_radius"] or player_pos[1] < thr):
            m["state"] = "patrol"
        if m["state"] == "chase":
            m["pos"], _ = _toward(m["pos"], player_pos, sp["chase_speed"] / TICK)
        else:
            m["pos"], arrived = _toward(m["pos"], m["waypoints"][m["target_idx"]], sp["patrol_speed"] / TICK)
            if arrived:
                m["target_idx"] = 1 - m["target_idx"]
        m["pos"] = _clamp(t, sp, m["pos"])
    return just_free


def find_hit(t, monsters, player_pos, invuln_ticks, just_free):
    """Con gây hit ở bước này (gần nhất, hòa theo id) hoặc None."""
    if invuln_ticks > 0:
        return None
    species = t["monsters"]["species"]
    cands = []
    for m in monsters:
        sp = species[m["kind"]]
        if m["state"] == "recoil" or m["id"] in just_free or player_pos[1] < sp["depths"][0]:
            continue
        dist = math.dist(m["pos"], player_pos)
        if dist <= sp["hit_radius"]:
            cands.append((dist, id_key(m["id"]), m))
    if not cands:
        return None
    return min(cands, key=lambda c: c[:2])[2]


def start_recoil(t, m, player_pos):
    sp = t["monsters"]["species"][m["kind"]]
    dx, dd = m["pos"][0] - player_pos[0], m["pos"][1] - player_pos[1]
    n = math.hypot(dx, dd)
    m["recoil_dir"] = [dx / n, dd / n] if n > 0 else [1.0, 0.0]
    m["state"] = "recoil"
    m["state_ticks_left"] = sp["recoil_ticks"]
