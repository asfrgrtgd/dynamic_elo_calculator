# elo_diff_fast.py  ―  差分再実行アルゴリズム・高速＆正確版
from collections import deque
from math import pow

class EloDiff:
    __slots__ = ("N", "rating", "matches", "hist", "etable")

    K      = 32          # K‑factor
    LIMIT  = 4000        # Δ のテーブル範囲（–4000..+4000）

    def __init__(self, n_players: int):
        self.N       = n_players
        self.rating  = [1500] * n_players
        self.matches = []                          # [winner, loser, deleted?]
        self.hist    = [[] for _ in range(n_players)]  # (match_id, rating_before)
        # 期待勝率テーブル（index = Δ + LIMIT）
        self.etable  = [1.0 / (1.0 + pow(10.0, d / 400.0))
                        for d in range(-self.LIMIT, self.LIMIT + 1)]

    # ---------------- 内部ユーティリティ ----------------
    def _expected(self, delta: int) -> float:
        """delta = opponentRating - selfRating"""
        if   delta < -self.LIMIT: delta = -self.LIMIT
        elif delta >  self.LIMIT: delta =  self.LIMIT
        return self.etable[delta + self.LIMIT]

    def _apply_win(self, w: int, l: int, mid: int) -> None:
        rw, rl  = self.rating[w], self.rating[l]
        Ew      = self._expected(rl - rw)          # ← 符号修正
        change  = round(self.K * (1.0 - Ew))
        self.rating[w] = rw + change
        self.rating[l] = rl - change

        self.hist[w].append((mid, rw))
        self.hist[l].append((mid, rl))

    # ---------------- 公開 API ----------------
    def win(self, winner: int, loser: int) -> None:
        mid = len(self.matches)
        self._apply_win(winner, loser, mid)
        self.matches.append([winner, loser, False])

    def delete(self, mid: int) -> None:
        if mid >= len(self.matches) or self.matches[mid][2]:
            return                                     # 無効な / 二重削除
        self.matches[mid][2] = True                    # フラグ立て

        # 1) 影響プレイヤー & 試合を DFS で列挙
        affected_p, affected_m = set(), set()
        stack = deque(self.matches[mid][:2])           # winner, loser
        while stack:
            p = stack.pop()
            if p in affected_p: continue
            affected_p.add(p)

            for m, _ in self.hist[p]:
                if m >= mid and not self.matches[m][2]:
                    if m != mid: affected_m.add(m)
                    w, l, _ = self.matches[m]
                    stack.extend((w, l))

        # 2) レート巻き戻し & 履歴 truncate
        for p in affected_p:
            lst = self.hist[p]
            i   = 0
            while i < len(lst) and lst[i][0] < mid:
                i += 1
            if i < len(lst):
                self.rating[p] = lst[i][1]   # M 直前の rating
                del lst[i:]                  # M 以降をまるごと削除

        # 3) 影響試合を時系列で再実行
        for m in sorted(affected_m):
            w, l, _ = self.matches[m]
            self._apply_win(w, l, m)

    def showrate(self) -> list[int]:
        return self.rating.copy()
