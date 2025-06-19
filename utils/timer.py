import time

class Timer:
    def __init__(self):
        self.timestamps = [("开始", time.time())]

    def mark(self, label):
        self.timestamps.append((label, time.time()))

    def report(self):
        import logging
        logging.info("📊 [计时统计]")
        base = self.timestamps[0][1]
        for i, (label, t) in enumerate(self.timestamps):
            if i == 0:
                continue
            delta = (t - self.timestamps[i - 1][1]) * 1000
            total = (t - base) * 1000
            logging.info(f"🟡 {label:<15} +{delta:.2f} ms    总计: {total:.2f} ms")

