# plugin/debouncer.py

"""
🔁 Debouncer - 防抖器插件

用于控制某个函数在短时间内只执行最后一次调用（避免频繁重复执行）。
适合用在数据库变更后、连续用户输入后等场景，防止浪费资源。

用法：
    debouncer = Debouncer(delay=1.5)  # 1.5秒防抖延迟

    def refresh_scheduler():
        print("刷新调度器！")

    # 在需要触发防抖逻辑的地方调用：
    debouncer.call(refresh_scheduler)
"""

import threading

class Debouncer:
    def __init__(self, delay=1.0):
        """
        初始化防抖器
        :param delay: 延迟时间（秒），默认为1.0秒
        """
        self.delay = delay
        self.timer = None

    def call(self, func, *args, **kwargs):
        """
        调用函数，防抖执行
        :param func: 目标函数
        :param args: 位置参数
        :param kwargs: 关键字参数
        """
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(self.delay, func, args=args, kwargs=kwargs)
        self.timer.start()

