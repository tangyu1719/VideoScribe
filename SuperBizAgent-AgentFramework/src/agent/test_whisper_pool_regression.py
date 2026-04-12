# -*- coding: utf-8 -*-
"""Whisper 池借还语义回归：与 video_gui 中 Queue 用法一致（不加载真实模型）。"""
from __future__ import annotations

import queue
import threading
import time
import unittest


class TestWhisperPoolQueue(unittest.TestCase):
    def test_max_parallel_equals_pool_size(self):
        n = 3
        q: queue.Queue = queue.Queue(maxsize=n)
        for i in range(n):
            q.put(("w%d" % i, i))

        concurrent = {"n": 0}
        lock = threading.Lock()
        peak = [0]

        def worker():
            slot = q.get(timeout=5)
            with lock:
                concurrent["n"] += 1
                peak[0] = max(peak[0], concurrent["n"])
            time.sleep(0.05)
            with lock:
                concurrent["n"] -= 1
            q.put_nowait(slot)

        threads = [threading.Thread(target=worker) for _ in range(6)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(peak[0], n, "同时持有槽位数不应超过池大小")
        self.assertEqual(q.qsize(), n, "归还后池应满")


if __name__ == "__main__":
    unittest.main()
