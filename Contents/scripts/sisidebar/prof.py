# -*- coding: utf-8 -*-
# 関数計測
import functools
import time
from collections import defaultdict

try:
    import cProfile as profile
    import pstats
except:
    pass


def profileFunction(sortKey="time", rows=30):
    def _(f):
        @functools.wraps(_)
        def __(*fargs, **fkwargs):
            prof = profile.Profile()
            ret = prof.runcall(f, *fargs, **fkwargs)
            pstats.Stats(prof).strip_dirs().sort_stats(sortKey).print_stats(
                rows
            )

            return ret

        return __

    return _


# 周回カウンター


class LapCounter:
    lap_times = 0
    lap_list = []

    def __init__(self):
        self.start = time.time()

    def count(self, string=""):
        self.end = time.time()
        lap_str = (
            "lap_time :",
            string,
            self.lap_times,
            ":",
            self.end - self.start,
        )
        self.lap_list.append(lap_str)
        self.lap_times += 1
        self.start = time.time()

    def lap_print(self, print_flag=True, window=None):
        total_time = time.time() - self.all_start

        if window:
            out_put_time = "{:.5f}".format(total_time)
            # ウィンドウに計算時間表示
            try:
                window.time_label.setText(
                    "- Calculation Time - " + out_put_time + " sec"
                )
            except Exception as e:
                e.message
                pass

        if print_flag:  # 表示するかどうかをグローバル変数で管理
            print("----------------------------------")
            for lap_time in self.lap_list:
                print(lap_time)
            print("total_time :", total_time)

    def reset(self):
        self.all_start = time.time()
        self.start = time.time()
        self.lap_list = []


# 積算カウンター,同名文字列の処理時間を積算していく
# for文を細かく処理負荷解析したいときに


class IntegrationCounter:
    def __init__(self):
        self.start = time.time()
        self.integration_dict = defaultdict(lambda: 0)

    def count(self, string=""):
        self.end = time.time()
        self.integration_dict[string] += self.end - self.start
        self.start = time.time()

    def integration_print(self, print_flag=True, window=None):
        for string, integration in self.integration_dict.items():
            print("Integration time :", string, integration)

    def reset(self):
        self.all_start = time.time()
        self.start = time.time()
        self.lap_list = []
