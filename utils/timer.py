from ..core.logger import logger
import time

class Timer:
    def __init__(self):
        self.timestamps = [("开始", time.time())]

    def mark(self, label: str):
        """记录一个新的时间戳"""
        self.timestamps.append((label, time.time()))

    def report(self):
        """输出所有记录的时间间隔"""
        logger.info("📊 [计时统计]")
        base = self.timestamps[0][1]
        for i, (label, t) in enumerate(self.timestamps):
            if i == 0:
                continue
            delta = (t - self.timestamps[i - 1][1]) * 1000  # 当前段耗时
            total = (t - base) * 1000  # 累计总耗时
            logger.info(f"🟡 {label:<15} +{delta:.2f} ms    总计: {total:.2f} ms")
