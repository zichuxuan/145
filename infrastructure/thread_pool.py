import logging
from PyQt6.QtCore import QObject, QThreadPool, QRunnable, pyqtSlot, pyqtSignal

class Worker(QRunnable):
    """
    通用工作线程类
    用于将阻塞操作（如 HTTP 请求）放入线程池执行
    """
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    @pyqtSlot()
    def run(self):
        """执行传入的任务函数"""
        try:
            self.fn(*self.args, **self.kwargs)
        except Exception as e:
            logging.error(f"Worker 任务执行失败: {e}")

class ThreadPoolManager(QObject):
    """
    线程池管理器基础设施层
    封装 QThreadPool，确保 UI 线程不因网络 IO 阻塞
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'pool'):
            super().__init__()
            self.pool = QThreadPool.globalInstance()
            # 根据 RK3588 的 8 核性能，可以适当增加线程数
            self.pool.setMaxThreadCount(8)
            self.logger = logging.getLogger("ThreadPoolManager")

    def start(self, fn, *args, **kwargs):
        """将函数任务提交到线程池"""
        worker = Worker(fn, *args, **kwargs)
        self.pool.start(worker)
        self.logger.debug(f"已向线程池提交新任务: {fn.__name__}")

# 全局单例
thread_pool = ThreadPoolManager()
