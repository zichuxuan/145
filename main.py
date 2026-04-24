import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication

# 导入各层组件
from infrastructure.mqtt_client import MqttClient
from services.device_service import DeviceService
from services.plc_control_service import PlcControlService
from viewmodels.device_viewmodel import DeviceViewModel
from views.main_window import MainWindow

from utils.config import config_manager

def setup_logging():
    log_file = Path(__file__).resolve().parent / "err.log"
    log_format = (
        "%(asctime)s | %(levelname)s | %(name)s | %(threadName)s | "
        "%(filename)s:%(lineno)d | %(message)s"
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(log_format))

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format))

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

def main():
    setup_logging()
    
    # 0. 使用 ConfigManager 获取配置
    config = config_manager._config
    
    # 1. 初始化应用
    app = QApplication(sys.argv)
    
    # 设置全局样式，特别是修复 QMessageBox 字体问题
    app.setStyleSheet("""
        QMessageBox {
            background-color: #1A1F26;
            border: 1px solid #2A3038;
        }
        QMessageBox QLabel {
            color: white;
            font-size: 24px;
            min-width: 400px;
            min-height: 100px;
        }
        QMessageBox QPushButton {
            background-color: #007AFF;
            color: white;
            border-radius: 8px;
            padding: 12px 30px;
            font-size: 20px;
            min-width: 120px;
        }
        QMessageBox QPushButton:hover {
            background-color: #0062CC;
        }
    """)
    
    # 2. 基础设施层实例化
    mqtt_cfg = config.get("mqtt", {})
    mqtt_client = MqttClient(
        host=mqtt_cfg.get("host", "localhost"),
        port=mqtt_cfg.get("port", 1883),
        username=mqtt_cfg.get("username"),
        password=mqtt_cfg.get("password"),
        client_id=mqtt_cfg.get("client_id", "hmi_terminal")
    )
    
    # 3. 业务服务层实例化
    device_service = DeviceService()
    plc_control_service = PlcControlService()
    
    # 4. ViewModel 层实例化 (注入基础设施和服务)
    device_vm = DeviceViewModel(mqtt_client, device_service, plc_control_service)
    
    # 5. View 层实例化
    window = MainWindow(device_vm)
    
    # 6. 显示窗口并启动循环
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
