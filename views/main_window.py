import logging

from PyQt6.QtWidgets import QMainWindow, QMessageBox, QStackedWidget
from views.production_overview import ProductionOverview
from views.smart_production import SmartProduction
from views.components.dialogs import PasswordDialog

class MainWindow(QMainWindow):
    """HMI 桌面客户端的主窗口容器。
    
    采用 QStackedWidget 管理主要页面（总览页和智能生产页）的层级关系。
    接收并响应 ViewModel 的基础状态信号（如 MQTT 连接状态、全局错误）。
    """
    def __init__(self, vm):
        super().__init__()
        self.vm = vm
        self.logger = logging.getLogger("MainWindow")
        self._init_ui()
        self._bind_viewmodel()

    def _init_ui(self):
        self.setWindowTitle("智能终端监控系统")
        # 设置窗口为全屏显示
        self.showFullScreen()
        self.setStyleSheet("background-color: #0B0E14;")

        # 使用 QStackedWidget 来管理不同的页面
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # 初始化主页面
        self.production_overview = ProductionOverview(self.vm)
        self.production_overview.secret_triggered.connect(self._show_password_dialog)
        self.stacked_widget.addWidget(self.production_overview)

        # 初始化运维设置页面
        self.smart_production = SmartProduction(self.vm)
        self.smart_production.exit_btn.clicked.connect(self._exit_smart_production)
        self.stacked_widget.addWidget(self.smart_production)

        self.stacked_widget.setCurrentWidget(self.production_overview)

    def _show_password_dialog(self):
        """显示密码输入框"""
        dialog = PasswordDialog(self)
        if dialog.exec():
            # 密码验证成功，跳转到智能生产页面
            self.stacked_widget.setCurrentWidget(self.smart_production)

    def _exit_smart_production(self):
        """退出智能生产页面，返回总览"""
        self.stacked_widget.setCurrentWidget(self.production_overview)

    def _bind_viewmodel(self):
        """绑定 ViewModel 信号"""
        self.vm.mqtt_status_changed.connect(self.update_mqtt_status)
        self.vm.telemetry_updated.connect(self.update_telemetry_ui)
        self.vm.error_occurred.connect(self._show_error)

    def update_mqtt_status(self, connected: bool):
        # 可以在 ProductionOverview 中添加一个状态指示器
        pass

    def update_telemetry_ui(self, data: dict):
        """实时更新界面数据"""
        # 这里可以将数据传递给 ProductionOverview 进行展示
        # 目前 ProductionOverview 使用的是模拟数据，后续可以根据 data 更新
        pass

    def _show_error(self, message: str):
        if isinstance(message, str) and message.startswith("API 错误:"):
            self.logger.warning("静默忽略 API 错误弹窗: %s", message)
            return
        QMessageBox.critical(self, "系统错误", message)
