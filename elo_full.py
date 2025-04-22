"""elo_full.py
単純全再計算 (B) 版の Elo レーティング管理クラス
取り消し後は全試合を 0 から順に再実行
"""

from math import pow


class EloFull:
    """全再計算アルゴリズム (B)"""

    __slots__ = ("N", "matches")

    def __init__(self, n_players: int) -> None:
        self.N = n_players
        # matches = [ [winner, loser, is_deleted] ]
        self.matches: list[list[int | bool]] = []

    # ------------------------------------------------------------------ #
    @staticmethod
    def _expected(ra: int, rb: int) -> float:
        return 1.0 / (1.0 + pow(10.0, (rb - ra) / 400.0))

    # ------------------------------------------------------------------ #
    # public API
    # ------------------------------------------------------------------ #
    def win(self, a: int, b: int) -> None:
        """0‑indexed のプレイヤー a が b に勝った"""
        self.matches.append([a, b, False])

    def delete(self, match_id: int) -> None:
        """試合 match_id を取消。is_deleted フラグを立てるだけ"""
        if 0 <= match_id < len(self.matches):
            self.matches[match_id][2] = True

    def showrate(self) -> list[int]:
        """全試合を 0 から再計算して最新 rating を返す"""
        rating = [1500] * self.N
        for a, b, deleted in self.matches:
            if deleted:
                continue
            ra, rb = rating[a], rating[b]
            ea = self._expected(ra, rb)
            rating[a] = round(ra + 32.0 * (1.0 - ea))
            rating[b] = round(rb - 32.0 * (1.0 - ea))
        return rating
