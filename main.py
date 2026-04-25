"""
明日方舟：斗蛐蛐 计分板 - Backend
FastAPI + WebSocket real-time state sync with strong consistency
"""
import json
import asyncio
import re
import copy
import time
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")


class GameState:
    def __init__(self):
        self.reset_game()
        self._version = 0
        self._lock = asyncio.Lock()
        self._prev_snapshot = None

    def _bump(self):
        self._version += 1

    def _snapshot(self):
        self._prev_snapshot = {
            "game_active": self.game_active,
            "current_round": self.current_round,
            "total_rounds": self.total_rounds,
            "round_stake": self.round_stake,
            "round_phase": self.round_phase,
            "correct_answer": self.correct_answer,
            "players": copy.deepcopy(self.players),
            "history": copy.deepcopy(self.history),
        }

    def reset_game(self):
        self.game_active = False
        self.current_round = 0
        self.total_rounds = 10
        self.round_stake = 0
        self.round_phase = "idle"
        self.correct_answer = None
        self.players: dict = {}
        self.history: list = []
        self.timer_start = 0
        self.timer_duration = 300
        self.timer_expired = False

    def rollback(self) -> bool:
        if not self._prev_snapshot:
            return False
        self._bump()
        snap = self._prev_snapshot
        self._prev_snapshot = None
        self.game_active = snap["game_active"]
        self.current_round = snap["current_round"]
        self.total_rounds = snap["total_rounds"]
        self.round_stake = snap["round_stake"]
        self.round_phase = "voting"
        self.correct_answer = None
        self.players = snap["players"]
        self.history = snap["history"]
        self.timer_expired = False
        self.timer_start = time.time()
        return True

    def start_game(self):
        self._bump()
        self.game_active = True
        self.current_round = 1
        self.round_stake = 0
        self.round_phase = "waiting"
        self.correct_answer = None
        self.history = []
        self._prev_snapshot = None
        self.timer_expired = False
        for p in self.players.values():
            p["score"] = 10000
            p["choice"] = None
            p["all_in"] = False
            p["eliminated"] = False
            p["confirmed"] = False

    def set_stake(self, stake: int):
        self._bump()
        self.round_stake = stake
        self.round_phase = "voting"
        self._prev_snapshot = None
        self.timer_start = time.time()
        self.timer_expired = False
        for p in self.players.values():
            p["choice"] = None
            p["all_in"] = False
            p["confirmed"] = False

    def all_confirmed(self) -> bool:
        active = [p for p in self.players.values() if not p["eliminated"]]
        if not active:
            return False
        return all(p.get("confirmed") for p in active)

    def set_answer(self, answer: str):
        self._snapshot()
        self._bump()
        self.correct_answer = answer
        self.round_phase = "revealed"
        results = []
        for uid, p in self.players.items():
            if p["eliminated"]:
                continue
            choice = p["choice"]
            if choice is None or choice == "watch":
                results.append({"uid": uid, "name": p["name"],
                                "choice": choice or "watch", "result": "watch", "change": 0})
                continue
            if choice == answer:
                if p["all_in"]:
                    invested = p["score"]
                    change = invested
                    p["score"] += change
                    results.append({"uid": uid, "name": p["name"], "choice": choice,
                                    "result": "win", "change": change, "all_in": True})
                else:
                    change = self.round_stake
                    p["score"] += change
                    results.append({"uid": uid, "name": p["name"], "choice": choice,
                                    "result": "win", "change": change, "all_in": False})
            else:
                if p["all_in"]:
                    invested = p["score"]
                    p["score"] = 0
                    p["eliminated"] = True
                    results.append({"uid": uid, "name": p["name"], "choice": choice,
                                    "result": "eliminated", "change": -invested, "all_in": True})
                else:
                    change = min(self.round_stake, p["score"])
                    p["score"] = max(0, p["score"] - change)
                    results.append({"uid": uid, "name": p["name"], "choice": choice,
                                    "result": "lose", "change": -change, "all_in": False})
        self.history.append({"round": self.current_round, "stake": self.round_stake,
                             "answer": answer, "results": results})
        self._check_all_eliminated()

    def _check_all_eliminated(self):
        if self.players and all(p["eliminated"] for p in self.players.values()):
            self.game_active = False
            self.round_phase = "idle"

    def next_round(self) -> bool:
        self._bump()
        self._prev_snapshot = None
        if self.current_round >= self.total_rounds:
            self.game_active = False
            self.round_phase = "idle"
            return False
        self.current_round += 1
        self.round_stake = 0
        self.round_phase = "waiting"
        self.correct_answer = None
        self.timer_expired = False
        for p in self.players.values():
            p["choice"] = None
            p["all_in"] = False
            p["confirmed"] = False
        return True

    def end_game(self):
        self._bump()
        self.game_active = False
        self.round_phase = "idle"

    def add_player(self, uid: str, name: str) -> str | None:
        if uid in self.players:
            return None
        self._bump()
        self.players[uid] = {"name": name, "score": 10000,
                             "choice": None, "all_in": False, "eliminated": False,
                             "confirmed": False}
        return uid

    def vote(self, uid: str, choice: str, all_in: bool = False) -> bool:
        if uid not in self.players or self.round_phase != "voting":
            return False
        p = self.players[uid]
        if p["eliminated"] or p.get("confirmed"):
            return False
        if choice == "watch":
            all_in = False
        else:
            if p["score"] < self.round_stake:
                all_in = True
            elif all_in:
                if self.current_round < 6:
                    all_in = False
        self._bump()
        p["choice"] = choice
        p["all_in"] = all_in
        return True

    def confirm_vote(self, uid: str) -> bool:
        if uid not in self.players or self.round_phase != "voting":
            return False
        p = self.players[uid]
        if p["eliminated"] or p["choice"] is None or p.get("confirmed"):
            return False
        self._bump()
        p["confirmed"] = True
        return True

    def can_all_in(self, uid: str) -> bool:
        if uid not in self.players:
            return False
        p = self.players[uid]
        if p["eliminated"] or p["score"] <= 0:
            return False
        if self.current_round >= 6:
            return True
        return p["score"] < self.round_stake

    def get_unconfirmed(self) -> list:
        return [p["name"] for p in self.players.values()
                if not p["eliminated"] and not p.get("confirmed")]

    def check_timer(self) -> bool:
        if self.round_phase != "voting" or self.timer_expired:
            return False
        elapsed = time.time() - self.timer_start
        if elapsed >= self.timer_duration:
            self.timer_expired = True
            for p in self.players.values():
                if not p["eliminated"] and not p.get("confirmed"):
                    if p["choice"] is None:
                        p["choice"] = "watch"
                    p["confirmed"] = True
            self._bump()
            return True
        return False

    def to_dict(self, *, for_player: str | None = None) -> dict:
        players = {}
        for uid, p in self.players.items():
            d = {"name": p["name"], "score": p["score"],
                 "eliminated": p["eliminated"], "all_in": p.get("all_in", False),
                 "can_all_in": self.can_all_in(uid),
                 "confirmed": p.get("confirmed", False),
                 "choice": p["choice"]}
            players[uid] = d
        active = [p for p in self.players.values() if not p["eliminated"]]
        confirmed_list = [p for p in active if p.get("confirmed")]
        all_confirmed_val = len(active) > 0 and len(confirmed_list) == len(active)
        elapsed = time.time() - self.timer_start if self.timer_start and self.round_phase == "voting" else 0
        remaining = max(0, self.timer_duration - elapsed) if self.round_phase == "voting" else 0
        return {
            "version": self._version,
            "game_active": self.game_active,
            "current_round": self.current_round,
            "total_rounds": self.total_rounds,
            "round_stake": self.round_stake,
            "round_phase": self.round_phase,
            "correct_answer": self.correct_answer,
            "can_rollback": self._prev_snapshot is not None and self.round_phase == "revealed",
            "all_confirmed": all_confirmed_val,
            "timer_remaining": int(remaining),
            "timer_expired": self.timer_expired,
            "players": players,
            "history": self.history,
            "voted_count": len(confirmed_list),
            "active_count": len(active),
        }


game = GameState()
# uid -> WebSocket
all_ws: dict[str, WebSocket] = {}

UID_RE = re.compile(r'^[A-Za-z0-9_-]{2,16}$')


async def broadcast():
    payload_cache = {}
    # Each player gets their own view
    for uid, ws in list(all_ws.items()):
        try:
            if uid not in payload_cache:
                payload_cache[uid] = json.dumps({"type": "state",
                                                  "data": game.to_dict(for_player=uid)})
            await ws.send_text(payload_cache[uid])
        except Exception:
            del all_ws[uid]


# ── HTTP ────────────────────────────────────────────────────

@app.get("/")
async def serve_index():
    return FileResponse("index.html")

app.mount("/", StaticFiles(directory="."), name="static")


# ── Timer background task ───────────────────────────────────

async def timer_loop():
    while True:
        await asyncio.sleep(1)
        if game.round_phase == "voting" and not game.timer_expired:
            if game.check_timer():
                await broadcast()


# ── WebSocket ───────────────────────────────────────────────

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    uid: str | None = None
    is_admin = False
    try:
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)
            action = msg.get("action")

            # ── Join as player ──
            if action == "join":
                name = msg.get("name", "").strip()
                user_id = msg.get("user_id", "").strip()
                admin_pwd = msg.get("admin_password", "")

                if not name:
                    await ws.send_text(json.dumps({"type": "error", "message": "请输入昵称"}))
                    continue
                if not user_id or not UID_RE.match(user_id):
                    await ws.send_text(json.dumps({"type": "error",
                                                   "message": "ID需2-16位，仅限字母数字下划线横杠"}))
                    continue

                is_admin = admin_pwd == ADMIN_PASSWORD

                async with game._lock:
                    if user_id in game.players:
                        # If UID exists, check if the old connection is dead
                        if user_id in all_ws:
                            try:
                                await all_ws[user_id].close()
                            except Exception:
                                pass
                            del all_ws[user_id]
                        # Allow re-join for existing player
                        uid = user_id
                        all_ws[uid] = ws
                    else:
                        result = game.add_player(user_id, name)
                        if result is None:
                            await ws.send_text(json.dumps({"type": "error", "message": "该ID已被占用"}))
                            continue
                        uid = user_id
                        all_ws[uid] = ws

                await ws.send_text(json.dumps({"type": "joined", "user_id": uid,
                                               "is_admin": is_admin,
                                               "data": game.to_dict(for_player=uid)}))
                await broadcast()

            # ── Reconnect ──
            elif action == "reconnect":
                old = msg.get("user_id", "").strip()
                admin_pwd = msg.get("admin_password", "")
                if old and old in game.players:
                    async with game._lock:
                        uid = old
                        is_admin = admin_pwd == ADMIN_PASSWORD
                        if uid in all_ws:
                            try:
                                await all_ws[uid].close()
                            except Exception:
                                pass
                        all_ws[uid] = ws
                    await ws.send_text(json.dumps({"type": "reconnected", "user_id": uid,
                                                   "is_admin": is_admin,
                                                   "data": game.to_dict(for_player=uid)}))
                    await broadcast()
                else:
                    await ws.send_text(json.dumps({"type": "error", "message": "ID不存在，请重新加入"}))

            # ── Unlock admin (password check, no re-join) ──
            elif action == "unlock_admin":
                pwd = msg.get("password", "")
                if pwd == ADMIN_PASSWORD:
                    is_admin = True
                    await ws.send_text(json.dumps({"type": "admin_unlocked"}))
                else:
                    await ws.send_text(json.dumps({"type": "error", "message": "密码错误"}))

            # ── Sync ──
            elif action == "sync":
                if uid and uid in game.players:
                    await ws.send_text(json.dumps({"type": "state",
                                                   "data": game.to_dict(for_player=uid)}))

            # ── Vote ──
            elif action == "vote":
                if uid and uid in game.players:
                    async with game._lock:
                        ok = game.vote(uid, msg.get("choice"), msg.get("all_in", False))
                    if ok:
                        await broadcast()
                    else:
                        await ws.send_text(json.dumps({"type": "error", "message": "无法投票"}))

            # ── Confirm vote ──
            elif action == "confirm_vote":
                if uid and uid in game.players:
                    async with game._lock:
                        ok = game.confirm_vote(uid)
                    if ok:
                        await broadcast()
                    else:
                        await ws.send_text(json.dumps({"type": "error", "message": "无法确认"}))

            # ── Admin: start ──
            elif action == "start_game" and is_admin:
                async with game._lock:
                    game.start_game()
                await broadcast()

            # ── Admin: set stake ──
            elif action == "set_stake" and is_admin:
                try:
                    stake = int(msg.get("stake", 0))
                    if stake <= 0:
                        raise ValueError
                    async with game._lock:
                        game.set_stake(stake)
                    await broadcast()
                except (ValueError, TypeError):
                    await ws.send_text(json.dumps({"type": "error", "message": "无效积分"}))

            # ── Admin: set answer ──
            elif action == "set_answer" and is_admin:
                ans = msg.get("answer")
                if ans in ("left", "right"):
                    async with game._lock:
                        game.set_answer(ans)
                    await broadcast()

            # ── Admin: rollback ──
            elif action == "rollback" and is_admin:
                async with game._lock:
                    ok = game.rollback()
                if ok:
                    await broadcast()
                else:
                    await ws.send_text(json.dumps({"type": "error", "message": "无法回滚"}))

            # ── Admin: next round ──
            elif action == "next_round" and is_admin:
                async with game._lock:
                    game.next_round()
                await broadcast()

            # ── Admin: end game ──
            elif action == "end_game" and is_admin:
                async with game._lock:
                    game.end_game()
                await broadcast()

            # ── Admin: send reminder ──
            elif action == "send_reminder" and is_admin:
                reminder_text = msg.get("text", "请尽快确认你的选择！")
                unconfirmed = game.get_unconfirmed()
                for uid_key, ws_player in list(all_ws.items()):
                    p = game.players.get(uid_key)
                    if p and not p["eliminated"] and not p.get("confirmed"):
                        try:
                            await ws_player.send_text(json.dumps({"type": "reminder",
                                                                  "message": reminder_text}))
                        except Exception:
                            pass
                await ws.send_text(json.dumps({"type": "info",
                                               "message": f"已提醒: {', '.join(unconfirmed)}"}))

    except WebSocketDisconnect:
        if uid and uid in all_ws:
            del all_ws[uid]


@app.on_event("startup")
async def startup():
    asyncio.create_task(timer_loop())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
