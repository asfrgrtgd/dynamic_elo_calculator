"""test_algos.py
差分再実行 (A) と 全再計算 (B) の比較テスト & ベンチマーク
可変大規模ケース実行＋結果とテストケースをフォルダ保存（結果は txt）
"""

import argparse
import random
import time
import os
import datetime
import json
from elo_diff import EloDiff
from elo_full import EloFull


def generate_case(seed: int, n_players: int, n_ops: int) -> list[tuple]:
    """ランダムテストケースを生成して返す"""
    rnd = random.Random(seed)
    commands = []
    live_matches = []
    for _ in range(n_ops):
        choice = rnd.random()
        if choice < 0.6 or not live_matches:
            # win
            a = rnd.randrange(n_players)
            b = rnd.randrange(n_players)
            while b == a:
                b = rnd.randrange(n_players)
            commands.append(("win", a, b))
            live_matches.append(len(live_matches))
        elif choice < 0.8:
            # delete match
            m = rnd.choice(live_matches)
            commands.append(("delete", m))
        else:
            commands.append(("show",))
    return commands


def run_system(system, commands):
    """system に対して commands を実行し、各 show の結果を返す"""
    outputs = []
    for cmd in commands:
        if cmd[0] == "win":
            _, a, b = cmd
            system.win(a, b)
        elif cmd[0] == "delete":
            _, m = cmd
            system.delete(m)
        elif cmd[0] == "show":
            outputs.append(system.showrate())
    return outputs


def run_case(seed: int, n_players: int, n_ops: int = 300):
    commands = generate_case(seed, n_players, n_ops)

    # テストケース保存
    return commands, run_case_exec(commands, n_players)


def run_case_exec(commands, n_players):
    diff = EloDiff(n_players)
    full = EloFull(n_players)
    t0 = time.perf_counter()
    out_a = run_system(diff, commands)
    ta = time.perf_counter() - t0
    t1 = time.perf_counter()
    out_b = run_system(full, commands)
    tb = time.perf_counter() - t1
    assert out_a == out_b, "結果が一致しません"
    return ta, tb, out_b


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="差分再実行 (A) と 全再計算 (B) の比較テスト & ベンチマーク"
    )
    parser.add_argument(
        '--players', '-p', type=int, nargs='+',
        help='テストごとのプレイヤー数リストまたは単一値'
    )
    parser.add_argument(
        '--ops', '-o', type=int, nargs='+',
        help='テストごとの操作数リストまたは単一値'
    )
    parser.add_argument(
        '--seeds', '-s', type=int, nargs='+',
        help='テストごとの乱数シードリストまたは単一値'
    )
    parser.add_argument(
        '--num-cases', '-n', type=int,
        help='生成するテストケース数 (単一値指定時に有効)'
    )
    parser.add_argument(
        '--tag', '-t', type=str,
        help='保存フォルダに付与するユニークタグ (デフォルト: タイムスタンプ)'
    )
    args = parser.parse_args()

    # テストケース組み立て
    if args.num_cases:
        ncases = args.num_cases
        # players
        if args.players:
            if len(args.players) == 1:
                players_list = [args.players[0]] * ncases
            elif len(args.players) == ncases:
                players_list = args.players
            else:
                parser.error('players は単一値か num-cases と同数で指定してください')
        else:
            parser.error('num-cases 使用時は --players を必須指定')
        # ops
        if args.ops:
            if len(args.ops) == 1:
                ops_list = [args.ops[0]] * ncases
            elif len(args.ops) == ncases:
                ops_list = args.ops
            else:
                parser.error('ops は単一値か num-cases と同数で指定してください')
        else:
            parser.error('num-cases 使用時は --ops を必須指定')
        # seeds
        if args.seeds:
            if len(args.seeds) == 1:
                seeds_list = [args.seeds[0] + i for i in range(ncases)]
            elif len(args.seeds) == ncases:
                seeds_list = args.seeds
            else:
                parser.error('seeds は単一値か num-cases と同数で指定してください')
        else:
            seeds_list = list(range(1, ncases+1))
        cases = list(zip(seeds_list, players_list, ops_list))
    elif args.players and args.ops and args.seeds and \
         len(args.players)==len(args.ops)==len(args.seeds):
        cases = list(zip(args.seeds, args.players, args.ops))
    else:
        cases = [
            (1, 2, 20),
            (2, 10, 100),
            (3, 50, 300),
            (4, 100, 500),
            (5, 200, 800),
        ]

    # 保存ディレクトリ
    tag = args.tag or datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    base_dir = os.path.join('testcase', tag)
    os.makedirs(base_dir, exist_ok=True)
    # 結果ファイル (.txt)
    result_file = os.path.join(base_dir, 'results.txt')

    header = ['case', 'players', 'ops', 'diff(ms)', 'full(ms)', 'speed-up', 'ok']
    with open(result_file, 'w', encoding='utf-8') as rf:
        rf.write(' '.join(header) + '\n')
        total = len(cases)
        print(f"全 {total} 件のテストケースを実行します。\n")
        for idx, (seed, n_players, n_ops) in enumerate(cases, start=1):
            commands, (ta, tb, out_b) = run_case(seed, n_players, n_ops)
            speed = tb / ta if ta > 0 else float('inf')
            ok = '✓'
            # 結果書込み
            row = [str(seed), str(n_players), str(n_ops), f"{ta*1e3:.2f}", f"{tb*1e3:.2f}", f"{speed:.2f}×", ok]
            rf.write(' '.join(row) + '\n')
            print(f"テストケース {idx}/{total} 完了: seed={seed}, players={n_players}, ops={n_ops}, diff={ta*1e3:.2f}ms, full={tb*1e3:.2f}ms, speed-up={speed:.2f}×")
            # テストケース保存
            case_file = os.path.join(base_dir, f"case_{idx}.json")
            with open(case_file, 'w', encoding='utf-8') as cf:
                json.dump({'seed': seed, 'players': n_players, 'ops': n_ops, 'commands': commands, 'expected': out_b}, cf, ensure_ascii=False, indent=2)

    print(f"\n全テスト完了。結果を保存: {result_file}")
