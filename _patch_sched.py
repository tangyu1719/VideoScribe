# -*- coding: utf-8 -*-
from pathlib import Path
import textwrap

p = Path(r"F:\java\AIOPS\SuperBizAgent-release-2026-01-02\demo_wendanghua\SuperBizAgent-AgentFramework\src\agent\video_gui.py")
t = p.read_text(encoding="utf-8")

a = """        self.task_queue = []
        self.processing_queue = False
"""
b = """        self.task_queue = []
        self._task_queue_lock = threading.Lock()
        self._scheduler_start_lock = threading.Lock()
        self.processing_queue = False
"""
if a not in t:
    raise SystemExit("init task_queue block missing")
t = t.replace(a, b, 1)

# Insert helpers after update_queue_status's closing of method - find "def _pipeline_log"
marker = "    def _pipeline_log(self, message: str):"
helpers = '''    def _task_queue_len(self) -> int:
        with self._task_queue_lock:
            return len(self.task_queue)

    def _task_queue_append_unique(self, link: str) -> bool:
        with self._task_queue_lock:
            if link in self.task_queue:
                return False
            self.task_queue.append(link)
            return True

    def _task_queue_pop_front(self):
        with self._task_queue_lock:
            if not self.task_queue:
                return None
            return self.task_queue.pop(0)

    def _task_queue_remove_if_present(self, link: str) -> bool:
        with self._task_queue_lock:
            if link in self.task_queue:
                self.task_queue.remove(link)
                return True
            return False

    def _total_queued_work(self) -> int:
        return self._task_queue_len() + len(self.active_futures)

    def _pipeline_log(self, message: str):'''

if marker not in t:
    raise SystemExit("pipeline_log marker missing")
if "_task_queue_len" in t:
    raise SystemExit("already patched?")
t = t.replace(marker, helpers, 1)

# update_queue_status
old_uq = """            queue_length = len(self.task_queue)
            processing_status = "处理中" if self.processing_queue else "就绪"
            self.queue_status.config(text=f"队列：{queue_length} 个任务 | 状态：{processing_status}")"""
new_uq = """            pending = self._task_queue_len()
            running = len(self.active_futures)
            processing_status = "处理中" if self.processing_queue else "就绪"
            self.queue_status.config(
                text=f"队列：{pending} 待处理 + {running} 执行中 | 状态：{processing_status}"
            )"""
if old_uq not in t:
    raise SystemExit("update_queue_status body missing")
t = t.replace(old_uq, new_uq, 1)

# recover
old_r = """                if link not in self.task_queue:
                    self.task_queue.append(link)"""
new_r = """                self._task_queue_append_unique(link)"""
if t.count(old_r) < 1:
    raise SystemExit("recover append pattern missing")
t = t.replace(old_r, new_r, 1)

# tree queue position
old_tree = """                if link in self.task_queue:
                    pos = self.task_queue.index(link) + 1
                    queue_pos = f"第{pos}位"
                    if self.processing_queue and pos <= self.max_workers * 2:
                        queue_pos += " (执行中)\""""
new_tree = """                if link in self.active_futures:
                    queue_pos = "执行中"
                elif link in self.task_queue:
                    with self._task_queue_lock:
                        pos = self.task_queue.index(link) + 1
                    queue_pos = f"第{pos}位（待处理）\""""
if old_tree not in t:
    raise SystemExit("tree queue_pos missing")
t = t.replace(old_tree, new_tree, 1)

# Replace all remaining "if link not in self.task_queue:\n                        self.task_queue.append(link)" with append_unique
pat = """                    if link not in self.task_queue:
                        self.task_queue.append(link)"""
rep = """                    self._task_queue_append_unique(link)"""
c = t.count(pat)
if c == 0:
    raise SystemExit("continue append pattern 0")
t = t.replace(pat, rep)

# excel batch append
pat2 = """                        if link not in self.task_queue:
                            self.task_queue.append(link)"""
if pat2 not in t:
    raise SystemExit("excel append missing")
t = t.replace(pat2, """                        self._task_queue_append_unique(link)""", 1)

# add link queue full check and append
old_add = """        if len(self.task_queue) >= self.queue_max_size:
            messagebox.showwarning("提示", f"任务队列已满（当前大小：{len(self.task_queue)}，最大限制：{self.queue_max_size}）\\n请稍后再添加任务或调整队列大小限制")
            return

        # 添加到任务队列
        self.task_queue.append(link)"""
new_add = """        if self._total_queued_work() >= self.queue_max_size:
            messagebox.showwarning(
                "提示",
                f"任务队列已满（待处理+执行中：{self._total_queued_work()}，最大限制：{self.queue_max_size}）\\n请稍后再添加任务或调整队列大小限制",
            )
            return

        # 添加到任务队列
        self._task_queue_append_unique(link)"""
if old_add not in t:
    raise SystemExit("add link block missing")
t = t.replace(old_add, new_add, 1)

old_log_len = """        self.append_log(f"当前队列长度：{len(self.task_queue)}")
        
        try:
            # 自动开始处理队列
            if not self.processing_queue:
                self.start_queue_processing()
            else:
                self.append_log(
                    "当前仍有任务在处理中，本次链接已入队；上一批次正常结束后将自动处理后续任务（若长时间无进度，请重启程序）"
                )"""
new_log_len = """        self.append_log(f"当前待处理：{self._task_queue_len()}，执行中：{len(self.active_futures)}")

        try:
            # 自动开始处理队列（调度已运行时，新链接会在有空闲线程时自动开始）
            if not self.processing_queue:
                self.start_queue_processing()
            else:
                self.append_log("调度运行中：新链接已入队，将在有空闲线程时按顺序自动执行")"""
if old_log_len not in t:
    raise SystemExit("add link tail missing")
t = t.replace(old_log_len, new_log_len, 1)

# batch import log and start
old_bi = """                self.append_log(f"当前队列长度：{len(self.task_queue)}")
                
                # 自动开始处理队列
                if not self.processing_queue and new_links_count > 0:
                    self.start_queue_processing()"""
new_bi = """                self.append_log(f"当前待处理：{self._task_queue_len()}，执行中：{len(self.active_futures)}")
                
                # 自动开始处理队列（已在处理时由调度器自动取新任务）
                if new_links_count > 0 and not self.processing_queue:
                    self.start_queue_processing()"""
if old_bi not in t:
    raise SystemExit("batch import block missing")
t = t.replace(old_bi, new_bi, 1)

# batch_stop remove
old_bs = """                        if link in self.task_queue:
                            self.task_queue.remove(link)
                            self.update_queue_status()"""
new_bs = """                        if self._task_queue_remove_if_present(link):
                            self.update_queue_status()"""
if old_bs not in t:
    raise SystemExit("batch_stop remove missing")
t = t.replace(old_bs, new_bs, 1)

# move_task_in_queue - wrap body with lock
old_mv = """        try:
            if link not in self.task_queue:
                self.append_log(f"任务不在队列中：{link}")
                return False
            
            idx = self.task_queue.index(link)
            
            if direction == "up":
                if idx == 0:
                    self.append_log("任务已在队列最前面")
                    return False
                # 交换位置
                self.task_queue[idx], self.task_queue[idx-1] = self.task_queue[idx-1], self.task_queue[idx]
                self.append_log(f"任务已上移：{link}")
                
            elif direction == "down":
                if idx == len(self.task_queue) - 1:
                    self.append_log("任务已在队列最后面")
                    return False
                # 交换位置
                self.task_queue[idx], self.task_queue[idx+1] = self.task_queue[idx+1], self.task_queue[idx]
                self.append_log(f"任务已下移：{link}")
            
            else:
                self.append_log(f"未知的移动方向：{direction}")
                return False
            
            self.update_queue_status()
            return True
            
        except Exception as e:
            self.append_log(f"移动任务失败：{e}")
            return False"""
new_mv = """        try:
            with self._task_queue_lock:
                if link not in self.task_queue:
                    self.append_log(f"任务不在待处理队列中（可能正在执行）：{link}")
                    return False

                idx = self.task_queue.index(link)

                if direction == "up":
                    if idx == 0:
                        self.append_log("任务已在队列最前面")
                        return False
                    self.task_queue[idx], self.task_queue[idx - 1] = (
                        self.task_queue[idx - 1],
                        self.task_queue[idx],
                    )
                    self.append_log(f"任务已上移：{link}")

                elif direction == "down":
                    if idx == len(self.task_queue) - 1:
                        self.append_log("任务已在队列最后面")
                        return False
                    self.task_queue[idx], self.task_queue[idx + 1] = (
                        self.task_queue[idx + 1],
                        self.task_queue[idx],
                    )
                    self.append_log(f"任务已下移：{link}")

                else:
                    self.append_log(f"未知的移动方向：{direction}")
                    return False

            self.update_queue_status()
            return True

        except Exception as e:
            self.append_log(f"移动任务失败：{e}")
            return False"""
if old_mv not in t:
    raise SystemExit("move_task missing")
t = t.replace(old_mv, new_mv, 1)

# thread config info
old_info = """        info_text = f"系统CPU核心数：{self.cpu_count}\\n当前活跃线程数：{len(self.active_futures)}\\n当前队列长度：{len(self.task_queue)}\\n当前队列最大大小：{self.queue_max_size}\""""
new_info = """        info_text = (
            f"系统CPU核心数：{self.cpu_count}\\n"
            f"当前执行中任务数：{len(self.active_futures)}\\n"
            f"待处理队列长度：{self._task_queue_len()}\\n"
            f"队列最大大小：{self.queue_max_size}"
        )"""
if old_info not in t:
    raise SystemExit("info_text missing")
t = t.replace(old_info, new_info, 1)

# Replace entire start_queue_processing through threading.Thread start
start_old = """    # 开始队列处理
    def start_queue_processing(self):
        if not self.task_queue:
            self.append_log("队列为空，无需处理")
            self.update_queue_status()
            return
        
        if self.processing_queue:
            self.append_log("队列正在处理中")
            self.update_queue_status()
            return
        
        self.processing_queue = True
        self.update_queue_status()
        
        # 限制一次处理的任务数量，避免系统过载
        batch_size = min(len(self.task_queue), self.max_workers * 2)  # 每次处理的任务数量为线程数的2倍
        task_links = self.task_queue[:batch_size]  # 只处理批次内的任务
        remaining_tasks = self.task_queue[batch_size:]  # 剩余任务
        
        self.append_log(f"开始处理队列任务，本次批次：{len(task_links)} 个任务")
        self.append_log(f"使用线程池并行处理，最大线程数：{self.max_workers}")
        self.append_log(f"队列中剩余任务：{len(remaining_tasks)} 个")
        self.append_log("遵循先进先出原则，按照提交顺序处理任务")
        
        # 使用线程池并行处理任务，保持先进先出顺序
        tasks = []
        
        # 清空之前的活跃任务映射（必须是 dict，不能是 list，否则 active_futures[link] 会抛错导致整批任务中断）
        self.active_futures = {}
        self._pipeline_log(f"batch_start links={len(task_links)} workers={self.max_workers}")

        for i, link in enumerate(task_links):
            task_number = i + 1
            # 获取任务绑定的用户提示词和飞书文件夹路径
            task_prompt = ""
            feishu_folder_path = None
            for task in self.history.get("tasks", []):
                if task.get("link") == link:
                    task_prompt = task.get("user_prompt", "")
                    feishu_folder_path = task.get("feishu_folder_path")
                    break
            
            # 如果任务没有绑定提示词，使用全局的
            if not task_prompt:
                task_prompt = self.user_prompt_var.get().strip()
            
            self.append_log(f"提交任务 {task_number}/{len(task_links)} 到线程池：{link}")
            self.append_log(f"任务提示词：{task_prompt[:50]}{'...' if len(task_prompt) > 50 else ''}")
            if feishu_folder_path:
                self.append_log(f"飞书文件夹路径：{feishu_folder_path}")
            
            # 创建取消标志
            cancel_event = threading.Event()
            self.task_cancel_flags[link] = cancel_event
            
            # 提交任务到线程池
            future = self.executor.submit(self._run_pipeline_with_cancel, link, task_prompt, feishu_folder_path, cancel_event)
            tasks.append(future)
            self.active_futures[link] = future
        
        # 等待所有任务完成（带超时 + finally 解锁，避免永久卡在「处理中」）
        def wait_for_completion():
            timeout_sec = int(os.environ.get("PIPELINE_BATCH_TIMEOUT_SEC", "7200"))
            completed_count = 0
            total_tasks = len(tasks)
            self._pipeline_log(f"wait_start futures={total_tasks} timeout_sec={timeout_sec}")
            try:
                for future in concurrent.futures.as_completed(tasks, timeout=timeout_sec):
                    try:
                        future.result()
                        completed_count += 1
                        self.append_log(f"任务完成进度：{completed_count}/{total_tasks}")
                        self._pipeline_log(f"future_done {completed_count}/{total_tasks}")
                    except concurrent.futures.CancelledError:
                        completed_count += 1
                        self.append_log("任务已取消", "WARNING")
                        self._pipeline_log("future_cancelled")
                    except Exception as e:
                        completed_count += 1
                        self.append_log(f"任务执行异常：{type(e).__name__}: {e}", "ERROR")
                        self._pipeline_log(f"future_exc {type(e).__name__}: {e!r}")

                self.append_log("本批次任务处理完成")
                self._pipeline_log(f"batch_complete ok {completed_count}/{total_tasks}")

                for link in task_links:
                    if link in self.task_queue:
                        self.task_queue.remove(link)
                    self.task_cancel_flags.pop(link, None)
                    self.active_futures.pop(link, None)

                self.processing_queue = False
                self.update_queue_status()
                if self.task_queue:
                    self.append_log(f"队列中还有 {len(self.task_queue)} 个新任务，继续处理下一批次")
                    time.sleep(0.5)
                    try:
                        self.start_queue_processing()
                    except Exception as e2:
                        self.append_log(f"启动下一批次失败（已记录，程序继续运行）：{type(e2).__name__}: {e2}", "ERROR")
                        self._pipeline_log(f"start_next_batch_exc {e2!r}")
                        self.processing_queue = False
                        self.update_queue_status()
                else:
                    self.append_log("所有队列任务处理完成")

            except concurrent.futures.TimeoutError:
                self.append_log(f"本批次等待超时（{timeout_sec}s），未完成任务已尝试取消；队列可继续手动重试", "ERROR")
                self._pipeline_log(f"TimeoutError partial_done={completed_count}/{total_tasks}")
                for f in tasks:
                    if not f.done():
                        f.cancel()
                for link in task_links:
                    self.task_cancel_flags.pop(link, None)
                    self.active_futures.pop(link, None)
                self.processing_queue = False
                self.update_queue_status()
            except Exception as e:
                self.append_log(f"队列调度异常（程序继续运行）：{type(e).__name__}: {e}", "ERROR")
                import traceback
                tb = traceback.format_exc()
                self.append_log(tb, "ERROR")
                self._pipeline_log(f"wait_exc {type(e).__name__}: {e!r}")
                self.processing_queue = False
                self.update_queue_status()

        threading.Thread(target=wait_for_completion, daemon=True).start()
    """

start_new = textwrap.dedent('''
    # 开始队列处理（线程池滑动窗口：最多 max_workers 路并行，FIFO，新入队任务不必等整批结束）
    def start_queue_processing(self):
        with self._scheduler_start_lock:
            if self.processing_queue:
                self.append_log("队列调度已在运行，新任务将在有空闲线程时按顺序自动执行")
                self.update_queue_status()
                return
            if self._task_queue_len() == 0:
                self.append_log("队列为空，无需处理")
                self.update_queue_status()
                return
            self.processing_queue = True

        self.update_queue_status()
        self.append_log(
            f"启动队列调度：最大并行 {self.max_workers}，当前待处理 {self._task_queue_len()}（先进先出，接近 Java 线程池行为）"
        )
        self._pipeline_log(f"scheduler_start workers={self.max_workers} pending={self._task_queue_len()}")
        threading.Thread(target=self._queue_scheduler_loop, daemon=True).start()

    def _queue_scheduler_loop(self):
        """维持不超过 max_workers 个并发；有空槽即从队首取任务提交。"""
        import time as time_mod

        poll = float(os.environ.get("PIPELINE_SCHEDULER_POLL_SEC", "0.5"))
        timeout_sec = int(os.environ.get("PIPELINE_BATCH_TIMEOUT_SEC", "7200"))
        wall0 = time_mod.time()
        active = {}
        completed_count = 0

        def _submit_link(link: str) -> None:
            task_prompt = ""
            feishu_folder_path = None
            for task in self.history.get("tasks", []):
                if task.get("link") == link:
                    task_prompt = task.get("user_prompt", "")
                    feishu_folder_path = task.get("feishu_folder_path")
                    break
            if not task_prompt:
                task_prompt = self.user_prompt_var.get().strip()
            self.append_log(f"任务提示词：{task_prompt[:50]}{'...' if len(task_prompt) > 50 else ''}")
            if feishu_folder_path:
                self.append_log(f"飞书文件夹路径：{feishu_folder_path}")
            cancel_event = threading.Event()
            self.task_cancel_flags[link] = cancel_event
            fut = self.executor.submit(
                self._run_pipeline_with_cancel, link, task_prompt, feishu_folder_path, cancel_event
            )
            self.active_futures[link] = fut
            active[link] = fut
            self.append_log(
                f"提交到线程池（并行 {len(active)}/{self.max_workers}）：{link[:120]}{'...' if len(link) > 120 else ''}"
            )
            self._pipeline_log(f"submit active={len(active)}")
            self.update_queue_status()

        try:
            while True:
                while len(active) < self.max_workers:
                    link = self._task_queue_pop_front()
                    if link is None:
                        break
                    _submit_link(link)

                if not active:
                    if self._task_queue_len() == 0:
                        self.append_log("所有队列任务处理完成")
                        self._pipeline_log("scheduler_done all_complete")
                        break
                    time_mod.sleep(poll)
                    continue

                if time_mod.time() - wall0 > timeout_sec:
                    self.append_log(f"队列调度总超时（{timeout_sec}s），正在取消未完成任务", "ERROR")
                    self._pipeline_log(f"scheduler_timeout active={len(active)}")
                    for f in list(active.values()):
                        f.cancel()
                    for link in list(active.keys()):
                        active.pop(link, None)
                        self.task_cancel_flags.pop(link, None)
                        self.active_futures.pop(link, None)
                    break

                done, _ = concurrent.futures.wait(
                    set(active.values()),
                    timeout=poll,
                    return_when=concurrent.futures.FIRST_COMPLETED,
                )
                for fut in done:
                    link = None
                    for lk, ff in list(active.items()):
                        if ff is fut:
                            link = lk
                            break
                    if link is None:
                        continue
                    try:
                        fut.result()
                    except concurrent.futures.CancelledError:
                        self.append_log("任务已取消", "WARNING")
                        self._pipeline_log("future_cancelled")
                    except Exception as e:
                        self.append_log(f"任务执行异常：{type(e).__name__}: {e}", "ERROR")
                        self._pipeline_log(f"future_exc {type(e).__name__}: {e!r}")
                    finally:
                        completed_count += 1
                        active.pop(link, None)
                        self.task_cancel_flags.pop(link, None)
                        self.active_futures.pop(link, None)
                        self.append_log(
                            f"任务完成进度：{completed_count}（当前并行 {len(active)}/{self.max_workers}）"
                        )
                        self.update_queue_status()
        except Exception as e:
            self.append_log(f"队列调度异常：{type(e).__name__}: {e}", "ERROR")
            import traceback
            self.append_log(traceback.format_exc(), "ERROR")
            self._pipeline_log(f"scheduler_exc {type(e).__name__}: {e!r}")
        finally:
            self.processing_queue = False
            self.update_queue_status()
''')

if start_old not in t:
    raise SystemExit("start_queue_processing block missing")
t = t.replace(start_old, start_new, 1)

p.write_text(t, encoding="utf-8")
print("scheduler patch ok")
