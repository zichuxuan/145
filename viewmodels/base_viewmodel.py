from PyQt6.QtCore import QObject, pyqtSignal

class BaseViewModel(QObject):
    """
    ViewModel 基类
    定义了通用的状态信号
    """
    # 通用信号
    busy_changed = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self._is_busy = False

    @property
    def is_busy(self):
        return self._is_busy

    @is_busy.setter
    def is_busy(self, value: bool):
        if self._is_busy != value:
            self._is_busy = value
            self.busy_changed.emit(value)
