from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QGridLayout, QPushButton, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, QDateTime, pyqtSignal, QEvent
from PyQt6.QtGui import QIcon, QPixmap, QColor
import os
import time

from views.components.charts import LineChart, BarChart, StorageBar

class StatusCard(QFrame):
    """右侧设备状态卡片。

    用于展示某一类设备的总数、运行数以及对应图标。
    """
    def __init__(self, title, icon_path, total="99", running="99", icon_bg="#1890ff", parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #1A1F26;
                border: 1px solid #2A3038;
                border-radius: 12px;
            }}
        """)
        self.setFixedHeight(85)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        
        # 图标容器：通过独立圆形背景块增强图标辨识度。
        icon_container = QFrame()
        icon_container.setFixedSize(40, 40)
        icon_container.setStyleSheet(f"""
            QFrame {{
                background-color: {icon_bg};
                border-radius: 20px;
                border: none;
            }}
        """)
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(8, 8, 8, 8)
        
        icon_label = QLabel()
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_layout.addWidget(icon_label)
        
        layout.addWidget(icon_container)
        
        # 文本区域：上方标题，下方显示总数和运行数量。
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        title_label = QLabel(title)
        title_label.setStyleSheet("color: white; font-size: 15px; font-weight: bold; border: none;")
        info_layout.addWidget(title_label)
        
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)
        
        total_label = QLabel(f"总数 <font color='#FFFFFF'>{total}</font>")
        total_label.setStyleSheet("color: #8C8C8C; font-size: 12px; border: none;")
        stats_layout.addWidget(total_label)
        
        running_label = QLabel(f"运行 <font color='#FFFFFF'>{running}</font>")
        running_label.setStyleSheet("color: #8C8C8C; font-size: 12px; border: none;")
        stats_layout.addWidget(running_label)
        
        info_layout.addLayout(stats_layout)
        layout.addLayout(info_layout)
        layout.addStretch()

class ProductionOverview(QWidget):
    """生产总览页。

    页面主要由顶部标题区和下方网格内容区组成，内容区再拆分为：
    - 产线能耗折线图；
    - 智能仓储料位条；
    - 智能设备状态卡片；
    - 生产统计柱状图。
    """
    secret_triggered = pyqtSignal()
    
    def __init__(self, vm, parent=None):
        super().__init__(parent)
        self.vm = vm
        self.base_path = "/home/pi/project/hmi/resources/images/"
        # 记录 logo 点击时间，用于实现“短时间多次点击”的隐藏入口。
        self.click_times = []
        self._init_ui()
        
    def _init_ui(self):
        """构建总览页所有静态 UI。"""
        self.setObjectName("ProductionOverview")
        self.setStyleSheet("background-color: #0B0E14;")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 15, 25, 25)
        main_layout.setSpacing(20)
        
        # --- HEADER ---
        header_layout = QHBoxLayout()
        
        # Logo：除展示品牌外，也承担隐藏入口触发区域。
        logo_label = QLabel()
        logo_path = os.path.join(self.base_path, "logo.svg")
        if os.path.exists(logo_path):
            logo_label.setPixmap(QPixmap(logo_path).scaled(140, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo_label.setCursor(Qt.CursorShape.PointingHandCursor)
        logo_label.installEventFilter(self)
        header_layout.addWidget(logo_label)
        
        header_layout.addStretch()
        
        # 顶部页签当前仅做视觉展示，实际页面切换通常由上层容器接管。
        tabs_container = QFrame()
        tabs_container.setStyleSheet("""
            QFrame {
                background-color: #1A1F26;
                border-radius: 22px;
                padding: 4px;
            }
        """)
        tabs_layout = QHBoxLayout(tabs_container)
        tabs_layout.setContentsMargins(4, 4, 4, 4)
        tabs_layout.setSpacing(0)
        
        btn_overview = QPushButton("总览")
        btn_overview.setFixedSize(110, 36)
        btn_overview.setStyleSheet("""
            QPushButton {
                background-color: #1890ff;
                color: white;
                border-radius: 18px;
                font-weight: bold;
                font-size: 15px;
            }
        """)
        
        btn_smart_prod = QPushButton("智能生产")
        btn_smart_prod.setFixedSize(110, 36)
        btn_smart_prod.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #8C8C8C;
                border-radius: 18px;
                font-size: 15px;
            }
        """)
        
        tabs_layout.addWidget(btn_overview)
        tabs_layout.addWidget(btn_smart_prod)
        header_layout.addWidget(tabs_container)
        
        header_layout.addStretch()
        
        # 右上角通知按钮和实时时间。
        notif_btn = QPushButton()
        notif_btn.setFixedSize(44, 44)
        notif_path = os.path.join(self.base_path, "notification.svg")
        if os.path.exists(notif_path):
            notif_btn.setIcon(QIcon(notif_path))
        notif_btn.setStyleSheet("background-color: #1A1F26; border-radius: 22px; border: none;")
        header_layout.addWidget(notif_btn)
        
        self.time_label = QLabel()
        self.time_label.setStyleSheet("color: white; font-size: 16px; margin-left: 15px; font-family: 'Inter';")
        header_layout.addWidget(self.time_label)
        
        # 使用轻量 QTimer 每秒刷新一次界面时间。
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_time)
        self.timer.start(1000)
        self._update_time()
        
        main_layout.addLayout(header_layout)
        
        # --- CONTENT ---
        content_layout = QGridLayout()
        content_layout.setSpacing(20)
        
        # 左上：产线能耗趋势图。
        energy_card = self._create_card("产线能耗统计")
        energy_chart = LineChart()
        energy_card.layout().addWidget(energy_chart)
        content_layout.addWidget(energy_card, 0, 0)
        
        # 中上：多个缓存仓料位条并排展示。
        storage_card = self._create_card("智能仓储")
        storage_layout = QHBoxLayout()
        storage_layout.setSpacing(10)
        storage_layout.addWidget(StorageBar("三色缓存仓", 206, color="#1890ff"))
        storage_layout.addWidget(StorageBar("3A缓存仓", 601, color="#faad14"))
        storage_layout.addWidget(StorageBar("二级缓存仓", 498, color="#faad14"))
        storage_layout.addWidget(StorageBar("杂瓶缓存仓", 297, color="#1890ff"))
        storage_card.layout().addLayout(storage_layout)
        content_layout.addWidget(storage_card, 0, 1)
        
        # 右侧整列：设备状态卡片 + 紧急停止按钮。
        equip_container = QFrame()
        equip_container.setStyleSheet("background-color: #1A1F26; border-radius: 16px; border: 1px solid #2A3038;")
        equip_layout = QVBoxLayout(equip_container)
        equip_layout.setContentsMargins(15, 20, 15, 15)
        equip_layout.setSpacing(12)
        
        equip_title = QLabel("智能设备")
        equip_title.setStyleSheet("color: white; font-size: 18px; font-weight: bold; border: none; margin-bottom: 5px;")
        equip_layout.addWidget(equip_title)
        
        equip_layout.addWidget(StatusCard("输送设备", os.path.join(self.base_path, "icon_transport.svg"), total="12", running="10", icon_bg="#006D75"))
        equip_layout.addWidget(StatusCard("分拣设备", os.path.join(self.base_path, "icon_sorting.svg"), total="08", running="08", icon_bg="#096DD9"))
        equip_layout.addWidget(StatusCard("码垛设备", os.path.join(self.base_path, "rect_73.svg"), total="04", running="03", icon_bg="#722ED1"))
        equip_layout.addWidget(StatusCard("包装设备", os.path.join(self.base_path, "rect_74.svg"), total="06", running="06", icon_bg="#C41D7F"))
        
        equip_layout.addStretch()
        
        # 紧急停止按钮放在设备列底部，避免与主网格发生重叠。
        self.stop_btn = QPushButton("紧急停止\nSTOP")
        self.stop_btn.setFixedSize(180, 180)  # 通过大尺寸增强危险操作的视觉权重。
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF4D4F;
                color: white;
                border-radius: 90px;
                font-size: 22px;
                font-weight: bold;
                border: 12px solid #2A1A1A;
            }
            QPushButton:pressed {
                background-color: #D4380D;
            }
        """)
        equip_layout.addWidget(self.stop_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        equip_layout.addSpacing(10)
        
        content_layout.addWidget(equip_container, 0, 2, 2, 1)
        
        # 左下和中下：生产统计柱状图，跨两列布局。
        prod_card = self._create_card("生产统计")
        prod_chart = BarChart()
        prod_card.layout().addWidget(prod_chart)
        content_layout.addWidget(prod_card, 1, 0, 1, 2)
        
        # 通过拉伸因子控制三列宽度，尽量贴近设计稿比例。
        content_layout.setColumnStretch(0, 4)  # 折线图列
        content_layout.setColumnStretch(1, 4)  # 仓储列
        content_layout.setColumnStretch(2, 2)  # 设备列相对更窄
        content_layout.setRowStretch(0, 4)
        content_layout.setRowStretch(1, 4)
        
        main_layout.addLayout(content_layout)

    def _create_card(self, title):
        """创建统一风格的卡片容器，并附带标题。"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #1A1F26;
                border-radius: 16px;
                border: 1px solid #2A3038;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold; border: none;")
        layout.addWidget(title_label)
        
        return card

    def _update_time(self):
        """刷新右上角时间显示。"""
        current_time = QDateTime.currentDateTime().toString("yyyy/M/d  HH:mm:ss")
        self.time_label.setText(current_time)
        
    def eventFilter(self, source, event):
        """监听 logo 点击，识别隐藏入口触发手势。

        逻辑为 5 秒内累计点击 3 次即触发 `secret_triggered` 信号，
        由外部决定是否进入运维或其他隐藏页面。
        """
        if event.type() == QEvent.Type.MouseButtonPress:
            current_time = time.time()
            self.click_times.append(current_time)
            
            # 只保留最近 5 秒内的点击时间，形成一个滑动窗口。
            self.click_times = [t for t in self.click_times if current_time - t <= 5.0]
            
            if len(self.click_times) >= 3:
                # 触发后立即清空，避免后续一次点击继续误触发。
                self.click_times = []
                self.secret_triggered.emit()
                
        return super().eventFilter(source, event)
