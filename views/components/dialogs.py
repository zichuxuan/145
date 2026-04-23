from PyQt6.QtWidgets import (QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QFrame, QComboBox, QFormLayout,
                             QMessageBox, QTabWidget, QRadioButton, QButtonGroup, QGridLayout,
                             QDateEdit, QDateTimeEdit, QSpacerItem, QSizePolicy, QMenu, QStackedWidget,
                             QTableWidget, QTableWidgetItem, QHeaderView, QAbstractSpinBox)
from PyQt6.QtCore import Qt, QSize, QPoint, QDateTime
from PyQt6.QtGui import QColor, QFont, QIcon, QAction
import os
from utils.config import config_manager

class CategoryCascaderComboBox(QComboBox):
    """用于设备类别选择的两级级联下拉框。

    外部依旧按普通 QComboBox 取值，但弹出层改为 QMenu 子菜单，
    以便把“设备大类/具体设备”以更清晰的层级关系呈现给用户。
    """
    def __init__(self, categories, menu_style="", parent=None):
        super().__init__(parent)
        self._categories = categories or {}
        self._menu_style = menu_style
        self._populate_items()

    def set_categories(self, categories):
        """更新候选项，并尽量保留当前选中的值。"""
        self._categories = categories or {}
        current = self.currentText()
        self._populate_items()
        if current:
            idx = self.findText(current)
            if idx >= 0:
                self.setCurrentIndex(idx)

    def _populate_items(self):
        """把层级数据拍平成 `分类/条目` 文本，便于表单直接提交。"""
        self.clear()
        for category, items in self._categories.items():
            for item in items:
                self.addItem(f"{category}/{item}")

    def _select_value(self, value):
        """根据菜单选择结果更新当前值。

        如果值原本不存在，则补充到下拉项中，确保编辑回显的历史值也能被选中。
        """
        idx = self.findText(value)
        if idx >= 0:
            self.setCurrentIndex(idx)
            return
        self.addItem(value)
        self.setCurrentIndex(self.count() - 1)

    def showPopup(self):
        """重写下拉弹层，改为分组子菜单展示类别。"""
        menu = QMenu(self)
        if self._menu_style:
            menu.setStyleSheet(self._menu_style)
        menu.setFixedWidth(max(self.width(), 220))

        for category, items in self._categories.items():
            submenu = QMenu(str(category), menu)
            if self._menu_style:
                submenu.setStyleSheet(self._menu_style)
            submenu.setFixedWidth(max(self.width(), 220))
            for item in items:
                value = f"{category}/{item}"
                action = QAction(str(item), submenu)
                action.triggered.connect(lambda checked=False, v=value: self._select_value(v))
                submenu.addAction(action)
            menu.addMenu(submenu)

        menu.exec(self.mapToGlobal(QPoint(0, self.height())))

class PasswordDialog(QDialog):
    """运维入口的密码校验弹窗。"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("系统权限验证")
        self.setFixedSize(400, 260)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._init_ui()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # 如果点击的是自身（即弹窗外的透明区域），则关闭弹窗
            if self.childAt(event.pos()) is None:
                self.reject()
        super().mousePressEvent(event)

    def _init_ui(self):
        """构建密码弹窗的主体卡片、输入框和按钮。"""
        self.container = QFrame(self)
        self.container.setObjectName("pwdContainer")
        self.container.setFixedSize(400, 260)
        self.container.setStyleSheet("""
            QFrame#pwdContainer {
                background-color: #1A1F26;
                border: 1px solid #2A3038;
                border-radius: 16px;
            }
        """)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        title_label = QLabel("请输入运维管理密码")
        title_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold; border: none;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("请输入 6 位数字密码")
        self.password_input.setFixedSize(340, 50)
        self.password_input.setStyleSheet("""
            QLineEdit {
                background-color: #0B0E14;
                color: white;
                border: 1px solid #2A3038;
                border-radius: 8px;
                padding-left: 15px;
                font-size: 16px;
            }
            QLineEdit:focus {
                border: 1px solid #1890ff;
            }
        """)
        layout.addWidget(self.password_input)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #FF4D4F; font-size: 14px; border: none;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.error_label)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setFixedSize(160, 44)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #8C8C8C;
                border: 1px solid #2A3038;
                border-radius: 8px;
                font-size: 16px;
            }
            QPushButton:hover {
                color: white;
                background-color: rgba(255, 255, 255, 0.05);
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.confirm_btn = QPushButton("确认")
        self.confirm_btn.setFixedSize(160, 44)
        self.confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #1890ff;
                color: white;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                border: none;
            }
            QPushButton:pressed {
                background-color: #096dd9;
            }
        """)
        self.confirm_btn.clicked.connect(self.verify_password)
        btn_layout.addWidget(self.confirm_btn)

        layout.addLayout(btn_layout)

        if self.parent():
            p_rect = self.parent().geometry()
            self.move(p_rect.center().x() - 200, p_rect.center().y() - 130)

    def verify_password(self):
        """校验密码并通过 `accept/reject` 向外部返回结果。"""
        saved_pwd = config_manager.get("admin_password", "123456")
        if self.password_input.text() == saved_pwd:
            self.accept()
        else:
            self.error_label.setText("密码错误，请重新输入")
            self.password_input.clear()
            self.password_input.setFocus()

class DeviceDialog(QDialog):
    """设备新增/编辑弹窗。

    弹窗分为两部分：
    - 基础属性：采集设备主表字段；
    - 远程控制：采集通信参数和行为事件列表。
    最终通过 `get_data()` 输出统一结构，交给外部页面再转给 ViewModel。
    """
    # Figma Colors
    BG_COLOR = "#1C212B"
    INPUT_BG = "#2A313E"
    BORDER_COLOR = "#3B4252"
    ACCENT_BLUE = "#007AFF"
    TEXT_WHITE = "#FFFFFF"
    TEXT_GRAY = "#A0A0A0"
    DANGER_RED = "#FF4D4F"

    def __init__(self, mode="add", models=None, device_data=None, parent=None):
        super().__init__(parent)
        self.mode = mode
        self.models = models or []
        self.device_data = device_data or {}
        self._data = None
        self.setWindowTitle("新增设备" if self.mode == "add" else "设备编辑")
        if parent:
            p_top_left = parent.mapToGlobal(QPoint(0, 0))
            self.setGeometry(p_top_left.x(), p_top_left.y(), parent.width(), parent.height())
        else:
            self.setFixedSize(1120, 720)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 统一样式定义，便于整个弹窗保持一致的视觉规范。
        self.label_style = f"color: #E2E8F0; font-size: 16px; border: none;"
        self.field_style = f"""
            QLineEdit, QDateEdit, QDateTimeEdit, QComboBox {{
                background-color: {self.INPUT_BG};
                color: white;
                border: 1px solid {self.BORDER_COLOR};
                border-radius: 6px;
                padding-left: 12px;
                font-size: 14px;
            }}
            QLineEdit:focus, QDateEdit:focus, QDateTimeEdit:focus, QComboBox:focus {{
                border: 1px solid {self.ACCENT_BLUE};
            }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox::down-arrow {{ image: none; }}
        """
        self.menu_style = f"""
            QMenu {{
                background-color: {self.INPUT_BG};
                color: white;
                border: 1px solid {self.BORDER_COLOR};
                border-radius: 10px;
                padding: 6px;
                font-size: 14px;
            }}
            QMenu::item {{ padding: 10px 12px; border-radius: 8px; min-width: 180px; }}
            QMenu::item:selected {{ background-color: {self.BORDER_COLOR}; }}
        """
        self.radio_style = f"""
            QRadioButton {{ color: #E2E8F0; font-size: 16px; border: none; background: transparent; }}
            QRadioButton::indicator {{ width: 16px; height: 16px; border-radius: 8px; border: 1px solid #64748B; background: transparent; }}
            QRadioButton::indicator:checked {{ background: {self.ACCENT_BLUE}; border: 4px solid {self.BG_COLOR}; }}
        """

        self._init_ui()
        self._populate_from_device()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # 点击内容卡片以外的遮罩区域时关闭弹窗
            if not self.container.geometry().contains(event.pos()):
                self.reject()
                return
        super().mousePressEvent(event)

    def _init_ui(self):
        """搭建设备弹窗骨架，包括标题、页签、内容区和底部提交按钮。"""
        self.container = QFrame(self)
        self.container.setObjectName("mainContainer")
        self.container.setFixedSize(1120, 720)
        self.container.setStyleSheet(f"""
            QFrame#mainContainer {{
                background-color: {self.BG_COLOR};
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 16px;
            }}
        """)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(24)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel(self.windowTitle())
        title_label.setStyleSheet(f"color: {self.TEXT_WHITE}; font-size: 24px; font-weight: bold; border: none;")
        header_layout.addStretch()
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Tabs
        tabs_layout = QHBoxLayout()
        tabs_layout.setSpacing(16)

        self.base_tab_btn = QPushButton("基础属性")
        self.base_tab_btn.setFixedSize(110, 36)
        self.base_tab_btn.clicked.connect(lambda: self.switch_tab(0))
        tabs_layout.addWidget(self.base_tab_btn)

        self.remote_tab_btn = QPushButton("远程控制")
        self.remote_tab_btn.setFixedSize(110, 36)
        self.remote_tab_btn.clicked.connect(lambda: self.switch_tab(1))
        tabs_layout.addWidget(self.remote_tab_btn)

        tabs_layout.addStretch()
        layout.addLayout(tabs_layout)

        # Stacked Widget
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self.stack)

        self._init_base_tab_ui()
        self._init_remote_tab_ui()

        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"background: transparent; color: {self.DANGER_RED}; font-size: 14px; border: none;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.error_label)

        # Footer Button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        primary_text = "新增设备" if self.mode == "add" else "保存"
        self.confirm_btn = QPushButton(primary_text)
        self.confirm_btn.setFixedSize(120, 48)
        self.confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.ACCENT_BLUE};
                color: white;
                border-radius: 12px;
                font-size: 16px;
                border: none;
            }}
            QPushButton:pressed {{ background-color: #0056B3; }}
        """)
        self.confirm_btn.clicked.connect(self._on_confirm)
        btn_layout.addWidget(self.confirm_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.switch_tab(0)

        self.container.move((self.width() - self.container.width()) // 2, (self.height() - self.container.height()) // 2)

    def switch_tab(self, index):
        """切换页签，并同步更新页签按钮高亮状态。"""
        self.stack.setCurrentIndex(index)
        active_style = f"""
            QPushButton {{
                background-color: {self.ACCENT_BLUE};
                color: white;
                border-radius: 18px;
                font-size: 16px;
                border: none;
            }}
        """
        inactive_style = f"""
            QPushButton {{
                background-color: transparent;
                color: {self.TEXT_GRAY};
                border-radius: 18px;
                font-size: 16px;
                border: none;
            }}
        """
        self.base_tab_btn.setStyleSheet(active_style if index == 0 else inactive_style)
        self.remote_tab_btn.setStyleSheet(active_style if index == 1 else inactive_style)

    def _create_datetime_input(self):
        """创建统一样式的时间选择控件，精确到分钟。"""
        widget = QDateTimeEdit()
        widget.setDisplayFormat("yyyy-MM-dd HH:mm")
        widget.setCalendarPopup(True)
        widget.setDateTime(QDateTime.currentDateTime())
        widget.setFixedHeight(44)
        widget.setStyleSheet(self.field_style)
        widget.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        widget.setKeyboardTracking(False)
        widget.setReadOnly(True)
        return widget

    def _set_datetime_value(self, widget, value):
        """兼容常见时间字符串格式，把值安全回填到时间控件。"""
        text = str(value or "").strip()
        if not text:
            widget.setDateTime(QDateTime.currentDateTime())
            return

        for fmt in ("yyyy-MM-dd HH:mm", "yyyy-MM-dd HH:mm:ss", "yyyy-MM-dd"):
            parsed = QDateTime.fromString(text, fmt)
            if parsed.isValid():
                widget.setDateTime(parsed)
                return

        parsed = QDateTime.fromString(text, Qt.DateFormat.ISODate)
        if parsed.isValid():
            widget.setDateTime(parsed)
            return

        widget.setDateTime(QDateTime.currentDateTime())

    def _get_datetime_value(self, widget):
        """统一输出分钟级时间字符串，便于接口提交。"""
        return widget.dateTime().toString("yyyy-MM-dd HH:mm")

    def _init_base_tab_ui(self):
        """初始化“基础属性”页。

        这里收集的是设备本身的静态/基础信息，后续会直接进入设备 payload。
        """
        page = QWidget()
        page.setStyleSheet("background: transparent; border: none;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        grid = QGridLayout()
        grid.setHorizontalSpacing(40)
        grid.setVerticalSpacing(20)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)

        # Left Column
        code_label = QLabel("设备编号")
        code_label.setStyleSheet(self.label_style)
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("保存后自动生成")
        self.code_input.setFixedHeight(44)
        self.code_input.setStyleSheet(self.field_style)
        self.code_input.setEnabled(False)
        grid.addWidget(code_label, 0, 0)
        grid.addWidget(self.code_input, 0, 1)

        category_label = QLabel("设备类别")
        category_label.setStyleSheet(self.label_style)
        self.category_combo = CategoryCascaderComboBox(
            {
                "输送设备": ["螺旋输送机", "皮带输送机", "板链输送机", "震动给料机", "吹瓶风机"],
                "筛选设备": ["滚筒筛", "智能光选机"],
                "处理设备": ["脱标机", "破碎机", "压包机"],
                "存储设备": ["普通料仓", "智能料仓"],
            },
            menu_style=self.menu_style,
        )
        self.category_combo.setFixedHeight(44)
        self.category_combo.setStyleSheet(self.field_style)
        self.category_combo.setCurrentText("输送设备/螺旋输送机")
        grid.addWidget(category_label, 1, 0)
        grid.addWidget(self.category_combo, 1, 1)

        line_label = QLabel("所属产线")
        line_label.setStyleSheet(self.label_style)
        self.line_input = QLineEdit()
        self.line_input.setPlaceholderText("请输入")
        self.line_input.setFixedHeight(44)
        self.line_input.setStyleSheet(self.field_style)
        grid.addWidget(line_label, 2, 0)
        grid.addWidget(self.line_input, 2, 1)

        start_date_label = QLabel("投运日期")
        start_date_label.setStyleSheet(self.label_style)
        self.start_date_input = self._create_datetime_input()
        grid.addWidget(start_date_label, 3, 0)
        grid.addWidget(self.start_date_input, 3, 1)

        runtime_label = QLabel("累计运行时长")
        runtime_label.setStyleSheet(self.label_style)
        self.runtime_input = QLineEdit()
        self.runtime_input.setPlaceholderText("请输入")
        self.runtime_input.setFixedHeight(44)
        self.runtime_input.setStyleSheet(self.field_style)
        grid.addWidget(runtime_label, 4, 0)
        grid.addWidget(self.runtime_input, 4, 1)

        vf_label = QLabel("是否变频")
        vf_label.setStyleSheet(self.label_style)
        vf_layout = QHBoxLayout()
        vf_layout.setSpacing(20)
        self.vf_radio_no = QRadioButton("无变频")
        self.vf_radio_yes = QRadioButton("变频控制")
        self.vf_radio_no.setChecked(True)
        for rb in (self.vf_radio_no, self.vf_radio_yes):
            rb.setStyleSheet(self.radio_style)
        vf_layout.addWidget(self.vf_radio_no)
        vf_layout.addWidget(self.vf_radio_yes)
        vf_layout.addStretch()
        vf_widget = QWidget()
        vf_widget.setLayout(vf_layout)
        grid.addWidget(vf_label, 5, 0)
        grid.addWidget(vf_widget, 5, 1)

        freq_label = QLabel("变频频率")
        freq_label.setStyleSheet(self.label_style)
        self.freq_input = QLineEdit()
        self.freq_input.setPlaceholderText("请输入")
        self.freq_input.setFixedHeight(44)
        self.freq_input.setStyleSheet(self.field_style)
        grid.addWidget(freq_label, 6, 0)
        grid.addWidget(self.freq_input, 6, 1)

        # Right Column
        enable_label = QLabel("启动设备")
        enable_label.setStyleSheet(self.label_style)
        enable_layout = QHBoxLayout()
        enable_layout.setSpacing(20)
        self.enable_radio_on = QRadioButton("开启")
        self.enable_radio_off = QRadioButton("禁用")
        self.enable_radio_on.setChecked(True)
        for rb in (self.enable_radio_on, self.enable_radio_off):
            rb.setStyleSheet(self.radio_style)
        enable_layout.addWidget(self.enable_radio_on)
        enable_layout.addWidget(self.enable_radio_off)
        enable_layout.addStretch()
        enable_widget = QWidget()
        enable_widget.setLayout(enable_layout)
        grid.addWidget(enable_label, 0, 2)
        grid.addWidget(enable_widget, 0, 3)

        name_label = QLabel("设备名称")
        name_label.setStyleSheet(self.label_style)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("请输入")
        self.name_input.setFixedHeight(44)
        self.name_input.setStyleSheet(self.field_style)
        grid.addWidget(name_label, 1, 2)
        grid.addWidget(self.name_input, 1, 3)

        location_label = QLabel("物理位置")
        location_label.setStyleSheet(self.label_style)
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("请输入")
        self.location_input.setFixedHeight(44)
        self.location_input.setStyleSheet(self.field_style)
        grid.addWidget(location_label, 2, 2)
        grid.addWidget(self.location_input, 2, 3)

        last_maint_label = QLabel("最近维护时间")
        last_maint_label.setStyleSheet(self.label_style)
        self.last_maint_input = self._create_datetime_input()
        grid.addWidget(last_maint_label, 3, 2)
        grid.addWidget(self.last_maint_input, 3, 3)

        picture_label = QLabel("设备图片")
        picture_label.setStyleSheet(self.label_style)
        self.picture_frame = QFrame()
        self.picture_frame.setFixedSize(80, 80)
        self.picture_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.INPUT_BG};
                border: 1px solid {self.BORDER_COLOR};
                border-radius: 12px;
            }}
        """)
        pic_layout = QVBoxLayout(self.picture_frame)
        pic_layout.setContentsMargins(0, 0, 0, 0)
        pic_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        plus_lbl = QLabel("+")
        plus_lbl.setStyleSheet("color: #94A3B8; font-size: 32px; font-weight: 300; border: none;")
        pic_layout.addWidget(plus_lbl)
        
        pic_container = QWidget()
        pic_container_layout = QHBoxLayout(pic_container)
        pic_container_layout.setContentsMargins(0, 0, 0, 0)
        pic_container_layout.addWidget(self.picture_frame)
        pic_container_layout.addStretch()
        grid.addWidget(picture_label, 4, 2, 3, 1, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        grid.addWidget(pic_container, 4, 3, 3, 1, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        layout.addLayout(grid)
        layout.addStretch()
        self.stack.addWidget(page)

    def _init_remote_tab_ui(self):
        """初始化“远程控制”页。

        该页既包含设备通信参数，也包含行为事件表格，是编辑远程控制能力的入口。
        """
        page = QWidget()
        page.setStyleSheet("background: transparent; border: none;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(24)

        # Control Mode & Settings
        top_layout = QHBoxLayout()
        top_layout.setSpacing(40)

        # Control Mode
        mode_layout = QHBoxLayout()
        mode_label = QLabel("控制模式")
        mode_label.setStyleSheet(self.label_style)
        mode_layout.addWidget(mode_label)
        mode_layout.addSpacing(20)
        self.plc_radio = QRadioButton("PLC控制")
        self.manual_radio = QRadioButton("手动控制")
        self.plc_radio.setChecked(True)
        for rb in (self.plc_radio, self.manual_radio):
            rb.setStyleSheet(self.radio_style)
        mode_layout.addWidget(self.plc_radio)
        mode_layout.addWidget(self.manual_radio)
        top_layout.addLayout(mode_layout)
        top_layout.addStretch()
        layout.addLayout(top_layout)

        # IP and Port
        settings_grid = QGridLayout()
        settings_grid.setHorizontalSpacing(40)
        settings_grid.setVerticalSpacing(20)
        settings_grid.setColumnStretch(1, 1)
        settings_grid.setColumnStretch(3, 1)

        ip_label = QLabel("IP地址")
        ip_label.setStyleSheet(self.label_style)
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("请输入")
        self.ip_input.setFixedHeight(44)
        self.ip_input.setStyleSheet(self.field_style)
        settings_grid.addWidget(ip_label, 0, 0)
        settings_grid.addWidget(self.ip_input, 0, 1)

        port_label = QLabel("端口")
        port_label.setStyleSheet(self.label_style)
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("请输入")
        self.port_input.setFixedHeight(44)
        self.port_input.setStyleSheet(self.field_style)
        settings_grid.addWidget(port_label, 0, 2)
        settings_grid.addWidget(self.port_input, 0, 3)
        layout.addLayout(settings_grid)

        # Action Events Header
        action_header = QHBoxLayout()
        action_title = QLabel("行为事件")
        action_title.setStyleSheet(f"color: {self.TEXT_WHITE}; font-size: 18px; font-weight: bold;")
        action_header.addWidget(action_title)
        action_header.addSpacing(20)
        
        self.add_event_btn = QPushButton("新增设备") # Following Figma text
        self.add_event_btn.setFixedSize(88, 36)
        self.add_event_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.INPUT_BG};
                color: {self.TEXT_WHITE};
                border: 1px solid {self.BORDER_COLOR};
                border-radius: 8px;
                font-size: 14px;
            }}
        """)
        self.add_event_btn.clicked.connect(self._append_empty_event_row)
        action_header.addWidget(self.add_event_btn)
        action_header.addStretch()
        layout.addLayout(action_header)

        # Table
        self.event_table = QTableWidget()
        self.event_table.setColumnCount(8)
        self.event_table.setHorizontalHeaderLabels(["序号", "事件名称", "点位地址", "功能码", "偏移量", "数据", "描述", "操作"])
        self.event_table.verticalHeader().setVisible(False)
        self.event_table.setShowGrid(False)
        self.event_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.event_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.event_table.setEditTriggers(QTableWidget.EditTrigger.AllEditTriggers)
        
        header = self.event_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setStyleSheet(f"""
            QHeaderView::section {{
                background-color: transparent;
                color: {self.TEXT_GRAY};
                padding: 12px;
                border: none;
                font-size: 14px;
                text-align: left;
            }}
        """)
        
        self.event_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: transparent;
                border: none;
                color: {self.TEXT_WHITE};
                font-size: 14px;
            }}
            QTableWidget::item {{
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            }}
        """)
        self.event_table.verticalHeader().setDefaultSectionSize(48)
        layout.addWidget(self.event_table)

        # Pagination
        pagination_layout = QHBoxLayout()
        pagination_layout.addStretch()
        
        # Simple pagination UI
        prev_btn = QPushButton("<")
        prev_btn.setFixedSize(32, 32)
        prev_btn.setStyleSheet(f"background: {self.INPUT_BG}; color: {self.TEXT_WHITE}; border: 1px solid {self.BORDER_COLOR}; border-radius: 4px;")
        pagination_layout.addWidget(prev_btn)
        
        for i in range(1, 6):
            p_btn = QPushButton(str(i))
            p_btn.setFixedSize(32, 32)
            if i == 1:
                p_btn.setStyleSheet(f"background: {self.ACCENT_BLUE}; color: white; border: none; border-radius: 4px;")
            else:
                p_btn.setStyleSheet(f"background: {self.INPUT_BG}; color: {self.TEXT_WHITE}; border: 1px solid {self.BORDER_COLOR}; border-radius: 4px;")
            pagination_layout.addWidget(p_btn)
            
        next_btn = QPushButton(">")
        next_btn.setFixedSize(32, 32)
        next_btn.setStyleSheet(f"background: {self.INPUT_BG}; color: {self.TEXT_WHITE}; border: 1px solid {self.BORDER_COLOR}; border-radius: 4px;")
        pagination_layout.addWidget(next_btn)
        
        pagination_layout.addStretch()
        layout.addLayout(pagination_layout)

        self.stack.addWidget(page)

    def _make_event_item(self, text, editable=True):
        """创建表格单元格，并统一设置居中与可编辑属性。"""
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if not editable:
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        return item

    def _create_delete_button_for_row(self, row):
        """为指定行生成删除按钮。

        删除后行号会变化，因此 `_refresh_event_row_meta()` 会重新创建按钮，
        以避免 lambda 闭包仍然引用旧行号。
        """
        del_btn = QPushButton("删除")
        del_btn.setFixedSize(72, 32)
        del_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 77, 79, 0.1);
                color: {self.DANGER_RED};
                border: 1px solid {self.DANGER_RED};
                border-radius: 8px;
                font-size: 14px;
            }}
        """)
        del_btn.clicked.connect(lambda _=False, r=row: self._delete_event_row(r))
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_layout.addWidget(del_btn)
        return btn_container

    def _append_event_row(self, values=None):
        """向行为事件表追加一行。

        `values` 只对应业务字段；序号列和操作列由界面自动维护。
        """
        row = self.event_table.rowCount()
        self.event_table.insertRow(row)
        event_values = values or ["", "", "", "", "", ""]
        for col in range(7):
            if col == 0:
                item = self._make_event_item(f"{row + 1:02d}", editable=False)
            else:
                text = event_values[col - 1] if col - 1 < len(event_values) else ""
                item = self._make_event_item(text, editable=True)
            self.event_table.setItem(row, col, item)
        self.event_table.setCellWidget(row, 7, self._create_delete_button_for_row(row))

    def _append_empty_event_row(self):
        """新增一个空事件行，并把焦点移动到事件名称列。"""
        self._append_event_row()
        last_row = self.event_table.rowCount() - 1
        self.event_table.setCurrentCell(last_row, 1)
        editable_item = self.event_table.item(last_row, 1)
        if editable_item:
            self.event_table.editItem(editable_item)

    def _delete_event_row(self, row):
        """删除事件行，并刷新行序号和删除按钮绑定。"""
        if row < 0 or row >= self.event_table.rowCount():
            return
        self.event_table.removeRow(row)
        self._refresh_event_row_meta()

    def _refresh_event_row_meta(self):
        """重建事件表的展示元数据。

        主要处理两件事：
        - 让序号列在删行后保持连续；
        - 重新绑定每一行删除按钮的目标行号。
        """
        for row in range(self.event_table.rowCount()):
            seq_item = self.event_table.item(row, 0)
            if seq_item is None:
                seq_item = self._make_event_item("", editable=False)
                self.event_table.setItem(row, 0, seq_item)
            seq_item.setText(f"{row + 1:02d}")
            seq_item.setFlags(seq_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.event_table.setCellWidget(row, 7, self._create_delete_button_for_row(row))

    def _populate_from_device(self):
        """编辑模式下把已有设备数据回填到表单。

        基础属性来自设备实例数据；
        远程控制配置来自 `device_data`；
        行为事件来自外部编辑入口提前查询好的 `actions`。
        """
        if not self.device_data:
            return
        
        # 基础属性：直接回显设备主数据。
        self.code_input.setText(str(self.device_data.get("device_code", "")))
        self.name_input.setText(str(self.device_data.get("device_name", "")))
        self.line_input.setText(str(self.device_data.get("production_line", "")))
        self.location_input.setText(str(self.device_data.get("location", "")))
        self._set_datetime_value(self.start_date_input, self.device_data.get("start_date", ""))
        self._set_datetime_value(self.last_maint_input, self.device_data.get("last_maint_time", ""))
        
        category = self.device_data.get("device_category") or self.device_data.get("category")
        if category:
            self.category_combo.setCurrentText(str(category))
            
        # 远程控制配置：回显通信参数和控制模式。
        remote_data = self.device_data.get("device_data", {})
        if isinstance(remote_data, dict):
            self.ip_input.setText(str(remote_data.get("ip", "")))
            self.port_input.setText(str(remote_data.get("port", "")))
            control_mode = remote_data.get("control_mode", "PLC")
            if control_mode == "PLC":
                self.plc_radio.setChecked(True)
            else:
                self.manual_radio.setChecked(True)

        # 行为事件：逐行还原到表格中，供用户继续编辑。
        actions = self.device_data.get("actions", [])
        self.event_table.setRowCount(0)
        if isinstance(actions, list):
            for action in actions:
                if not isinstance(action, dict):
                    continue
                command_params = action.get("action_command_params", {})
                if not isinstance(command_params, dict):
                    command_params = {}
                self._append_event_row([
                    str(action.get("action_name", "")),
                    str(command_params.get("point_address", "")),
                    str(command_params.get("function_code", "")),
                    str(command_params.get("offset", "")),
                    str(command_params.get("data", "")),
                    str(command_params.get("description", "")),
                ])

    def _collect_action_rows(self):
        """采集行为事件表格数据，转换为 API 可用结构。

        注意：
        - 序号列和操作列仅供界面展示，不参与提交；
        - 空事件名称行视为未填写，直接跳过；
        - 其余参数统一收口到 `action_command_params`。
        """
        actions = []
        for row in range(self.event_table.rowCount()):
            action_name_item = self.event_table.item(row, 1)
            point_address_item = self.event_table.item(row, 2)
            function_code_item = self.event_table.item(row, 3)
            offset_item = self.event_table.item(row, 4)
            data_item = self.event_table.item(row, 5)
            description_item = self.event_table.item(row, 6)

            action_name = (action_name_item.text().strip() if action_name_item else "")
            if not action_name:
                continue

            actions.append({
                "action_name": action_name,
                "action_command_params": {
                    "point_address": point_address_item.text().strip() if point_address_item else "",
                    "function_code": function_code_item.text().strip() if function_code_item else "",
                    "offset": offset_item.text().strip() if offset_item else "",
                    "data": data_item.text().strip() if data_item else "",
                    "description": description_item.text().strip() if description_item else "",
                },
            })
        return actions

    def _on_confirm(self):
        """校验输入并整理弹窗输出数据。

        这里不直接发请求，而是把 UI 输入转换成统一字典，
        由调用方在 `dialog.exec()` 成功后再交给 ViewModel 处理。
        """
        self.error_label.setText("")
        code = self.code_input.text().strip()
        name = self.name_input.text().strip()
        line = self.line_input.text().strip()
        ip = self.ip_input.text().strip()
        port = self.port_input.text().strip()

        if not name:
            self.error_label.setText("设备名称不能为空")
            return

        # 设备型号 ID 默认留空；编辑时沿用原值，避免误覆盖原有型号绑定。
        model_id = self.device_data.get("device_model_id", "")

        # 统一输出结构，供 SmartProduction -> DeviceViewModel -> DeviceService 使用。
        self._data = {
            "device_code": code,
            "device_name": name,
            "communication_protocol": "TCP",
            "production_line": line,
            "location": self.location_input.text().strip(),
            "start_date": self._get_datetime_value(self.start_date_input),
            "last_maint_time": self._get_datetime_value(self.last_maint_input),
            "device_category": self.category_combo.currentText(),
            "device_data": {
                "ip": ip,
                "port": port,
                # 单选按钮在界面上是中文，但提交给后端使用约定好的英文枚举值。
                "control_mode": "PLC" if self.plc_radio.isChecked() else "Manual"
            },
            "actions": self._collect_action_rows(),
        }
        if model_id not in ("", None):
            self._data["device_model_id"] = model_id
        self.accept()

    def get_data(self):
        """返回确认后的表单数据。"""
        return self._data
