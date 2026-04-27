import logging
import os
from functools import partial
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, QDateTime
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from utils.config import config_manager
from views.components.dialogs import DeviceDialog

# 导入拆分后的模块
from .smart_production_constants import (
    WORKFLOW_TYPE_OPTIONS,
)
from .smart_production_utils import (
    create_default_workflow_detail,
    extract_workflow_description,
    build_workflow_detail_payload,
    extract_canvas_detail
)
from .smart_production_canvas import (
    WorkflowCanvasEditor,
)

class SmartProduction(QWidget):
    """智能生产管理页面主容器。
    
    承载了工作流/流程配置列表页及新建、编辑的详情页（含表单和画布）。
    通过 QStackedWidget 实现多页切换（列表 <-> 详情 <-> 全屏画布），
    并与 DeviceViewModel 强绑定处理异步数据加载与提交。
    """

    def __init__(self, vm, parent=None):
        super().__init__(parent)
        self.vm = vm
        self.logger = logging.getLogger("SmartProduction")
        self.base_path = str(Path(__file__).resolve().parents[1] / "resources" / "images")
        self.menu_buttons = []
        self.device_models = []
        self.devices = []
        self.workflows = []
        self._pending_edit_device = None
        self._pending_workflow_mode = None
        self._editing_workflow_id = None
        self._draft_mode = False
        self._workflow_canvas_fullscreen = False

        self._init_ui()
        self._bind_viewmodel()

        self.vm.load_device_models()
        self.vm.load_devices()
        self.vm.load_workflows()

    def _bind_viewmodel(self):
        self.vm.devices_loaded.connect(self._on_devices_loaded)
        self.vm.device_models_loaded.connect(self._on_models_loaded)
        self.vm.device_actions_loaded.connect(self._on_device_actions_loaded)
        self.vm.device_operation_finished.connect(self._on_operation_finished)
        self.vm.workflows_loaded.connect(self._on_workflows_loaded)
        self.vm.workflow_detail_loaded.connect(self._on_workflow_detail_loaded)
        self.vm.workflow_operation_finished.connect(self._on_workflow_operation_finished)
        self.vm.error_occurred.connect(self._handle_viewmodel_error)

    def _handle_viewmodel_error(self, message: str):
        if isinstance(message, str) and message.startswith("API 错误:"):
            self.logger.warning("静默忽略 API 错误弹窗: %s", message)
            return
        QMessageBox.critical(self, "错误", message)

    def _init_ui(self):
        self.setObjectName("SmartProduction")
        self.setStyleSheet("background-color: #0B0E14;")

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(40, 30, 40, 40)
        self.main_layout.setSpacing(30)

        self.header_widget = QWidget()
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        self.exit_btn = QPushButton(" 退出")
        self.exit_btn.setFixedSize(160, 80)
        exit_icon_path = os.path.join(self.base_path, "exit.svg")
        if os.path.exists(exit_icon_path):
            self.exit_btn.setIcon(QIcon(exit_icon_path))
        self.exit_btn.setStyleSheet(
            """
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 40px;
                font-size: 32px;
            }
            QPushButton:pressed { background-color: rgba(255, 255, 255, 0.2); }
            """
        )
        header_layout.addWidget(self.exit_btn)
        header_layout.addStretch()

        title_label = QLabel("运维设置")
        title_label.setStyleSheet("color: white; font-size: 40px; font-weight: 500;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        self.time_label = QLabel()
        self.time_label.setStyleSheet("color: white; font-size: 24px;")
        header_layout.addWidget(self.time_label)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_time)
        self.timer.start(1000)
        self._update_time()
        self.header_widget.setLayout(header_layout)
        self.main_layout.addWidget(self.header_widget)

        self.content_layout = QHBoxLayout()
        self.content_layout.setSpacing(40)

        self.sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(20)
        self.menu_items = ["设备管理", "流程配置", "工艺配置"]
        for i, name in enumerate(self.menu_items):
            btn = QPushButton(name)
            btn.setFixedSize(204, 98)
            btn.clicked.connect(lambda checked, idx=i: self._on_menu_clicked(idx))
            self.menu_buttons.append(btn)
            sidebar_layout.addWidget(btn)
        sidebar_layout.addStretch()
        self.sidebar_widget.setLayout(sidebar_layout)
        self.content_layout.addWidget(self.sidebar_widget)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self._create_device_management_view())
        self.stacked_widget.addWidget(self._create_workflow_config_view())
        self.stacked_widget.addWidget(self._create_process_config_view())
        self.content_layout.addWidget(self.stacked_widget, stretch=1)
        self.main_layout.addLayout(self.content_layout)
        self._on_menu_clicked(0)

    def _on_menu_clicked(self, index):
        self.stacked_widget.setCurrentIndex(index)
        for i, btn in enumerate(self.menu_buttons):
            if i == index:
                btn.setStyleSheet(
                    """
                    QPushButton {
                        background-color: #007AFF;
                        color: white;
                        border-radius: 16px;
                        font-size: 32px;
                        border: none;
                    }
                    """
                )
            else:
                btn.setStyleSheet(
                    """
                    QPushButton {
                        background-color: rgba(255, 255, 255, 0.1);
                        color: white;
                        border-radius: 16px;
                        font-size: 32px;
                        border: 1px solid rgba(255, 255, 255, 0.2);
                    }
                    """
                )

    def _create_device_management_view(self):
        container = QFrame()
        container.setStyleSheet("background-color: rgba(255, 255, 255, 0.05); border-radius: 16px;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)

        top_bar = QHBoxLayout()
        table_title = QLabel("设备管理")
        table_title.setStyleSheet("color: white; font-size: 24px; font-weight: bold; background: transparent;")
        top_bar.addWidget(table_title)
        top_bar.addStretch()
        add_btn = QPushButton("+ 新增设备")
        add_btn.setFixedSize(160, 50)
        add_btn.setStyleSheet("background-color: #007AFF; color: white; border-radius: 8px; font-size: 18px;")
        add_btn.clicked.connect(self._on_add_device_clicked)
        top_bar.addWidget(add_btn)
        layout.addLayout(top_bar)

        self.device_table = QTableWidget(0, 5)
        self.device_table.setHorizontalHeaderLabels(["设备编号", "设备名称", "设备类型", "设备状态", "操作"])
        self.device_table.setStyleSheet(
            """
            QTableWidget { background-color: transparent; color: white; border: none; font-size: 18px; }
            QHeaderView::section { background-color: transparent; color: rgba(255, 255, 255, 0.6); padding: 10px; border: none; font-size: 20px; }
            QTableWidget::item { padding: 15px; border-bottom: 1px solid rgba(255, 255, 255, 0.1); }
            """
        )
        self.device_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.device_table.verticalHeader().setVisible(False)
        self.device_table.verticalHeader().setDefaultSectionSize(72)
        self.device_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.device_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.device_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout.addWidget(self.device_table)

        pagination_layout = QHBoxLayout()
        pagination_layout.addStretch()
        p_btn = QPushButton("1")
        p_btn.setFixedSize(40, 40)
        p_btn.setStyleSheet("background-color: #007AFF; color: white; border-radius: 8px; border: none;")
        pagination_layout.addWidget(p_btn)
        pagination_layout.addStretch()
        layout.addLayout(pagination_layout)
        return container

    def _create_workflow_config_view(self):
        self.workflow_config_container = QFrame()
        self.workflow_config_container.setStyleSheet("background-color: rgba(255,255,255,0.03); border-radius: 20px;")
        layout = QVBoxLayout(self.workflow_config_container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)
        self.workflow_config_layout = layout

        self.workflow_stack = QStackedWidget()
        self.workflow_stack.addWidget(self._create_workflow_list_page())
        self.workflow_stack.addWidget(self._create_workflow_designer_page())
        self.workflow_stack.addWidget(self._create_workflow_canvas_fullscreen_page())
        layout.addWidget(self.workflow_stack)
        return self.workflow_config_container

    def _create_workflow_list_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 10, 20, 20)
        layout.setSpacing(18)

        top_bar = QHBoxLayout()
        top_bar.addStretch()
        add_btn = QPushButton("添加流程")
        add_btn.setFixedSize(140, 56)
        add_btn.setStyleSheet(
            "background-color: rgba(255,255,255,0.1); color: white; border-radius: 14px; border: 1px solid rgba(255,255,255,0.18); font-size: 20px;"
        )
        add_btn.clicked.connect(self._open_create_workflow)
        top_bar.addWidget(add_btn)
        layout.addLayout(top_bar)

        self.workflow_table = QTableWidget(0, 4)
        self.workflow_table.setHorizontalHeaderLabels(["编号", "流程名称", "说明", "操作"])
        self.workflow_table.setStyleSheet(
            """
            QTableWidget { background-color: transparent; color: white; border: none; font-size: 18px; }
            QHeaderView::section { background-color: transparent; color: rgba(255,255,255,0.64); padding: 10px; border: none; font-size: 20px; }
            QTableWidget::item { padding: 18px; border-bottom: 1px solid rgba(255,255,255,0.08); }
            """
        )
        self.workflow_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.workflow_table.verticalHeader().setVisible(False)
        self.workflow_table.verticalHeader().setDefaultSectionSize(78)
        self.workflow_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.workflow_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.workflow_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout.addWidget(self.workflow_table)

        pager = QHBoxLayout()
        pager.addStretch()
        self.workflow_page_btn = QPushButton("1")
        self.workflow_page_btn.setFixedSize(40, 40)
        self.workflow_page_btn.setStyleSheet("background-color: #007AFF; color: white; border-radius: 8px; border: none;")
        pager.addWidget(self.workflow_page_btn)
        pager.addStretch()
        layout.addLayout(pager)
        return page

    def _create_workflow_designer_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 8, 16, 16)
        layout.setSpacing(20)

        top_bar = QHBoxLayout()
        self.workflow_back_btn = QPushButton(" 返回")
        self.workflow_back_btn.setFixedSize(120, 56)
        self.workflow_back_btn.setStyleSheet(
            "background-color: rgba(255,255,255,0.1); color: white; border-radius: 28px; border: 1px solid rgba(255,255,255,0.18); font-size: 22px;"
        )
        self.workflow_back_btn.clicked.connect(self._return_to_workflow_list)
        top_bar.addWidget(self.workflow_back_btn)
        top_bar.addStretch()

        title = QLabel("流程设计")
        title.setStyleSheet("color: white; font-size: 38px; font-weight: 600;")
        top_bar.addWidget(title)
        top_bar.addStretch()

        self.workflow_draft_btn = QPushButton("存草稿")
        self.workflow_save_btn = QPushButton("保存")
        for btn in (self.workflow_draft_btn, self.workflow_save_btn):
            btn.setFixedSize(120, 56)
            btn.setStyleSheet(
                "background-color: rgba(255,255,255,0.1); color: white; border-radius: 14px; border: 1px solid rgba(255,255,255,0.18); font-size: 20px;"
            )
        self.workflow_draft_btn.clicked.connect(lambda: self._submit_workflow(is_draft=True))
        self.workflow_save_btn.clicked.connect(lambda: self._submit_workflow(is_draft=False))
        top_bar.addWidget(self.workflow_draft_btn)
        top_bar.addSpacing(12)
        top_bar.addWidget(self.workflow_save_btn)
        layout.addLayout(top_bar)

        tab_row = QHBoxLayout()
        tab_row.addStretch()
        self.workflow_basic_tab_btn = QPushButton("基础属性")
        self.workflow_remote_tab_btn = QPushButton("远程控制")
        for btn in (self.workflow_basic_tab_btn, self.workflow_remote_tab_btn):
            btn.setFixedSize(170, 58)
            btn.clicked.connect(self._toggle_workflow_tab)
        self.workflow_basic_tab_btn.clicked.connect(lambda: self._set_workflow_tab(0))
        self.workflow_remote_tab_btn.clicked.connect(lambda: self._set_workflow_tab(1))
        tab_row.addWidget(self.workflow_basic_tab_btn)
        tab_row.addWidget(self.workflow_remote_tab_btn)
        tab_row.addStretch()
        layout.addLayout(tab_row)

        self.workflow_editor_stack = QStackedWidget()
        self.workflow_editor_stack.addWidget(self._create_workflow_basic_form())
        self.workflow_editor_stack.addWidget(self._create_workflow_canvas_page())
        layout.addWidget(self.workflow_editor_stack)
        self._set_workflow_tab(0)
        return page

    def _create_workflow_basic_form(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 20, 0, 0)
        layout.setSpacing(24)

        top_form = QHBoxLayout()
        top_form.setSpacing(28)

        left_form = QVBoxLayout()
        left_form.setSpacing(12)
        left_form.addWidget(self._create_field_label("流程名称"))
        self.workflow_name_input = QLineEdit()
        self.workflow_name_input.setPlaceholderText("请输入")
        self.workflow_name_input.setFixedHeight(58)
        self.workflow_name_input.setStyleSheet(self._input_style())
        left_form.addWidget(self.workflow_name_input)
        top_form.addLayout(left_form, 1)

        right_form = QVBoxLayout()
        right_form.setSpacing(12)
        right_form.addWidget(self._create_field_label("流程类型"))
        self.workflow_type_combo = QComboBox()
        self.workflow_type_combo.setFixedHeight(58)
        self.workflow_type_combo.setStyleSheet(self._input_style())
        for label, value in WORKFLOW_TYPE_OPTIONS:
            self.workflow_type_combo.addItem(label, value)
        right_form.addWidget(self.workflow_type_combo)
        top_form.addLayout(right_form, 1)
        layout.addLayout(top_form)

        status_title = self._create_field_label("启动状态")
        layout.addWidget(status_title)
        status_row = QHBoxLayout()
        status_row.setSpacing(24)
        self.workflow_status_group = QButtonGroup(self)
        self.workflow_enabled_radio = QRadioButton("开启")
        self.workflow_disabled_radio = QRadioButton("禁用")
        self.workflow_status_group.addButton(self.workflow_enabled_radio)
        self.workflow_status_group.addButton(self.workflow_disabled_radio)
        self.workflow_enabled_radio.setChecked(True)
        for radio in (self.workflow_enabled_radio, self.workflow_disabled_radio):
            radio.setStyleSheet("color: white; font-size: 18px;")
            status_row.addWidget(radio)
        status_row.addStretch()
        layout.addLayout(status_row)

        layout.addWidget(self._create_field_label("说明"))
        self.workflow_description_input = QTextEdit()
        self.workflow_description_input.setPlaceholderText("请输入")
        self.workflow_description_input.setMinimumHeight(240)
        self.workflow_description_input.setStyleSheet(self._input_style())
        layout.addWidget(self.workflow_description_input)
        layout.addStretch()
        return page

    def _create_workflow_canvas_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.workflow_canvas_editor = WorkflowCanvasEditor(self)
        self.workflow_canvas_editor.fullscreen_requested.connect(self._on_workflow_canvas_fullscreen_requested)
        self.workflow_canvas_normal_layout = layout
        layout.addWidget(self.workflow_canvas_editor)
        return page

    def _create_workflow_canvas_fullscreen_page(self):
        page = QWidget()
        page.setStyleSheet("background-color: #0B0E14;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        header = QHBoxLayout()
        self.workflow_fullscreen_back_btn = QPushButton("退出全屏")
        self.workflow_fullscreen_back_btn.setFixedSize(140, 52)
        self.workflow_fullscreen_back_btn.setStyleSheet(
            "background-color: rgba(255,255,255,0.1); color: white; border-radius: 26px; "
            "border: 1px solid rgba(255,255,255,0.18); font-size: 18px;"
        )
        self.workflow_fullscreen_back_btn.clicked.connect(self._exit_workflow_canvas_fullscreen)
        header.addWidget(self.workflow_fullscreen_back_btn)
        header.addStretch()

        title = QLabel("流程画布")
        title.setStyleSheet("color: white; font-size: 32px; font-weight: 600;")
        header.addWidget(title)
        header.addStretch()

        self.workflow_fullscreen_draft_btn = QPushButton("存草稿")
        self.workflow_fullscreen_save_btn = QPushButton("保存")
        for btn in (self.workflow_fullscreen_draft_btn, self.workflow_fullscreen_save_btn):
            btn.setFixedSize(120, 52)
            btn.setStyleSheet(
                "background-color: rgba(255,255,255,0.1); color: white; border-radius: 14px; "
                "border: 1px solid rgba(255,255,255,0.18); font-size: 18px;"
            )
        self.workflow_fullscreen_draft_btn.clicked.connect(lambda: self._submit_workflow(is_draft=True))
        self.workflow_fullscreen_save_btn.clicked.connect(lambda: self._submit_workflow(is_draft=False))
        header.addWidget(self.workflow_fullscreen_draft_btn)
        header.addSpacing(12)
        header.addWidget(self.workflow_fullscreen_save_btn)
        layout.addLayout(header)

        self.workflow_canvas_fullscreen_container = QWidget()
        self.workflow_canvas_fullscreen_layout = QVBoxLayout(self.workflow_canvas_fullscreen_container)
        self.workflow_canvas_fullscreen_layout.setContentsMargins(0, 0, 0, 0)
        self.workflow_canvas_fullscreen_layout.setSpacing(0)
        layout.addWidget(self.workflow_canvas_fullscreen_container, stretch=1)
        return page

    def _attach_workflow_canvas_editor(self, target_layout):
        if self.workflow_canvas_editor.parent() is not None:
            self.workflow_canvas_editor.setParent(None)
        target_layout.addWidget(self.workflow_canvas_editor)

    def _on_workflow_canvas_fullscreen_requested(self, is_fullscreen):
        if is_fullscreen:
            self._enter_workflow_canvas_fullscreen()
        else:
            self._exit_workflow_canvas_fullscreen()

    def _enter_workflow_canvas_fullscreen(self):
        """将画布组件切换到全屏模式。
        
        通过 setParent(None) 和重新 addWidget，把同一个 WorkflowCanvasEditor 实例
        从常规布局转移到全屏容器中，从而保留所有状态并利用整块屏幕空间。
        """
        if self._workflow_canvas_fullscreen:
            return
        self._workflow_canvas_fullscreen = True
        self._attach_workflow_canvas_editor(self.workflow_canvas_fullscreen_layout)
        self._apply_workflow_canvas_fullscreen_ui(True)
        self.workflow_canvas_editor.set_fullscreen_mode(True)
        self.workflow_stack.setCurrentIndex(2)

    def _exit_workflow_canvas_fullscreen(self):
        if not self._workflow_canvas_fullscreen:
            return
        self._workflow_canvas_fullscreen = False
        self._attach_workflow_canvas_editor(self.workflow_canvas_normal_layout)
        self._apply_workflow_canvas_fullscreen_ui(False)
        self.workflow_canvas_editor.set_fullscreen_mode(False)
        self.workflow_stack.setCurrentIndex(1)
        self._set_workflow_tab(1)

    def _apply_workflow_canvas_fullscreen_ui(self, is_fullscreen):
        self.header_widget.setVisible(not is_fullscreen)
        self.sidebar_widget.setVisible(not is_fullscreen)
        if is_fullscreen:
            self.main_layout.setContentsMargins(0, 0, 0, 0)
            self.main_layout.setSpacing(0)
            self.content_layout.setContentsMargins(0, 0, 0, 0)
            self.content_layout.setSpacing(0)
            self.workflow_config_layout.setContentsMargins(0, 0, 0, 0)
            self.workflow_config_container.setStyleSheet("background-color: #0B0E14; border-radius: 0px;")
        else:
            self.main_layout.setContentsMargins(40, 30, 40, 40)
            self.main_layout.setSpacing(30)
            self.content_layout.setContentsMargins(0, 0, 0, 0)
            self.content_layout.setSpacing(40)
            self.workflow_config_layout.setContentsMargins(20, 20, 20, 20)
            self.workflow_config_container.setStyleSheet("background-color: rgba(255,255,255,0.03); border-radius: 20px;")

    def _create_field_label(self, text):
        label = QLabel(text)
        label.setStyleSheet("color: white; font-size: 20px; font-weight: 500;")
        return label

    def _input_style(self):
        return (
            "QLineEdit, QTextEdit, QComboBox {"
            "background-color: rgba(255,255,255,0.08);"
            "color: white;"
            "border: 1px solid rgba(255,255,255,0.18);"
            "border-radius: 10px;"
            "padding: 10px 12px;"
            "font-size: 18px;"
            "}"
            "QComboBox QAbstractItemView { background-color: #1F2937; color: white; selection-background-color: #007AFF; }"
        )

    def _toggle_workflow_tab(self):
        sender = self.sender()
        if sender == self.workflow_remote_tab_btn:
            self._set_workflow_tab(1)
        else:
            self._set_workflow_tab(0)

    def _set_workflow_tab(self, index):
        if index != 1 and self._workflow_canvas_fullscreen:
            self._exit_workflow_canvas_fullscreen()
        self.workflow_editor_stack.setCurrentIndex(index)
        active_style = "background-color: #007AFF; color: white; border-radius: 18px; border: none; font-size: 22px;"
        inactive_style = "background-color: rgba(255,255,255,0.1); color: white; border-radius: 18px; border: 1px solid rgba(255,255,255,0.18); font-size: 22px;"
        self.workflow_basic_tab_btn.setStyleSheet(active_style if index == 0 else inactive_style)
        self.workflow_remote_tab_btn.setStyleSheet(active_style if index == 1 else inactive_style)

    def _open_create_workflow(self):
        self._pending_workflow_mode = None
        self._editing_workflow_id = None
        self._draft_mode = False
        self._exit_workflow_canvas_fullscreen()
        self._reset_workflow_editor()
        self.workflow_stack.setCurrentIndex(1)
        self._set_workflow_tab(0)

    def _open_edit_workflow(self, workflow):
        """进入“编辑工作流”模式。
        
        触发异步详情加载流程，并在回调时回显配置与画布。
        """
        if not isinstance(workflow, dict) or not workflow.get("id"):
            QMessageBox.warning(self, "错误", "流程数据无效，无法编辑")
            return
        self._pending_workflow_mode = "edit"
        self._editing_workflow_id = workflow.get("id")
        self.vm.load_workflow_detail(workflow.get("id"))

    def _on_workflow_detail_loaded(self, workflow_detail):
        """处理工作流详情加载完成的异步回调。
        
        回填详情数据到画布及基础配置表单，并切换至详情编辑页。
        """
        if self._pending_workflow_mode != "edit":
            return
        self._pending_workflow_mode = None
        self._exit_workflow_canvas_fullscreen()
        self._populate_workflow_editor(workflow_detail)
        self.workflow_stack.setCurrentIndex(1)
        self._set_workflow_tab(0)

    def _return_to_workflow_list(self):
        self._exit_workflow_canvas_fullscreen()
        self.workflow_stack.setCurrentIndex(0)
        self._pending_workflow_mode = None
        self._editing_workflow_id = None
        self._draft_mode = False

    def _reset_workflow_editor(self):
        self.workflow_name_input.clear()
        self.workflow_type_combo.setCurrentIndex(0)
        self.workflow_enabled_radio.setChecked(True)
        self.workflow_description_input.clear()
        self.workflow_canvas_editor.reset_zoom()
        self.workflow_canvas_editor.set_fullscreen_mode(False)
        self.workflow_canvas_editor.set_workflow_detail(create_default_workflow_detail())

    def _populate_workflow_editor(self, workflow):
        self._reset_workflow_editor()
        if not isinstance(workflow, dict):
            return
        self.workflow_name_input.setText(str(workflow.get("workflow_name") or ""))
        workflow_type = workflow.get("workflow_type")
        index = self.workflow_type_combo.findData(workflow_type)
        if index >= 0:
            self.workflow_type_combo.setCurrentIndex(index)
        enabled = bool(workflow.get("enable_or_not", 0))
        self.workflow_enabled_radio.setChecked(enabled)
        self.workflow_disabled_radio.setChecked(not enabled)
        self.workflow_description_input.setPlainText(extract_workflow_description(workflow))
        
        # 兼容读取 workflow_detail 的双层结构或旧单层结构
        canvas_detail = extract_canvas_detail(workflow.get("workflow_detail") or create_default_workflow_detail())
        self.workflow_canvas_editor.set_workflow_detail(canvas_detail)

    def _collect_workflow_payload(self, is_draft=False):
        """收集画布及表单内容，组装成要下发给后端的标准 payload。

        Args:
            is_draft (bool): 是否作为草稿保存（影响 enable_or_not 标记）。
        Returns:
            dict/None: 校验通过的参数字典，若缺失必填项则返回 None。
        """
        workflow_name = self.workflow_name_input.text().strip()
        if not workflow_name:
            QMessageBox.warning(self, "错误", "请输入流程名称")
            return None
        workflow_type = self.workflow_type_combo.currentData() or self.workflow_type_combo.currentText().strip()
        description = self.workflow_description_input.toPlainText().strip()
        enable_or_not = 0 if is_draft else (1 if self.workflow_enabled_radio.isChecked() else 0)
        
        # 建立双层结构的 workflow_detail
        canvas_detail = self.workflow_canvas_editor.get_workflow_detail()
        workflow_detail = build_workflow_detail_payload(canvas_detail)
        
        return {
            "workflow_name": workflow_name,
            "workflow_type": workflow_type,
            "info": description,
            "workflow_params": {
                "is_draft": bool(is_draft),
            },
            "workflow_detail": workflow_detail,
            "conditions": {},
            "enable_or_not": enable_or_not,
        }

    def _submit_workflow(self, is_draft=False):
        """执行保存工作流的异步请求。
        
        基于 self._editing_workflow_id 判断执行更新（update）或创建（add），
        并进入繁忙状态。
        """
        payload = self._collect_workflow_payload(is_draft=is_draft)
        if payload is None:
            return
        self._draft_mode = is_draft
        if self._editing_workflow_id:
            self.vm.update_workflow(self._editing_workflow_id, payload)
        else:
            self.vm.add_workflow(payload)

    def _on_workflow_operation_finished(self, success, msg):
        if success:
            message = "存草稿成功" if self._draft_mode else msg
            QMessageBox.information(self, "成功", message)
            self.vm.load_workflows()
            self._return_to_workflow_list()
        else:
            QMessageBox.warning(self, "失败", msg)

    def _on_workflows_loaded(self, workflows):
        self.workflows = self._normalize_devices(workflows)
        self._refresh_workflow_table()

    def _refresh_workflow_table(self):
        self.workflow_table.setRowCount(0)
        for workflow in self.workflows:
            row = self.workflow_table.rowCount()
            self.workflow_table.insertRow(row)
            row_id = str(workflow.get("id") or "")
            row_name = str(workflow.get("workflow_name") or "")
            row_desc = extract_workflow_description(workflow)
            values = [row_id, row_name, row_desc]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.workflow_table.setItem(row, col, item)

            actions_container = QWidget()
            actions_layout = QHBoxLayout(actions_container)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(12)
            actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            edit_btn = QPushButton("编辑")
            edit_btn.setFixedSize(92, 42)
            edit_btn.setStyleSheet(
                "background-color: rgba(255,255,255,0.12); color: white; border-radius: 10px; border: 1px solid rgba(255,255,255,0.16); font-size: 16px;"
            )
            edit_btn.clicked.connect(partial(self._open_edit_workflow, workflow))
            actions_layout.addWidget(edit_btn)

            delete_btn = QPushButton("删除")
            delete_btn.setFixedSize(92, 42)
            delete_btn.setStyleSheet(
                "background-color: rgba(239,68,68,0.12); color: #F87171; border-radius: 10px; border: 1px solid rgba(239,68,68,0.24); font-size: 16px;"
            )
            delete_btn.clicked.connect(partial(self._delete_workflow, workflow))
            actions_layout.addWidget(delete_btn)

            self.workflow_table.setCellWidget(row, 3, actions_container)

    def _delete_workflow(self, workflow):
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除流程“{workflow.get('workflow_name', '')}”吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.vm.delete_workflow(workflow.get("id"))

    def _normalize_devices(self, devices):
        if devices is None:
            return []
        if isinstance(devices, dict):
            for key in ("devices", "data", "items", "rows", "list", "workflows"):
                value = devices.get(key)
                if isinstance(value, list):
                    devices = value
                    break
            else:
                return [devices]
        if not isinstance(devices, (list, tuple)):
            return []
        return [item for item in devices if isinstance(item, dict)]

    def _on_devices_loaded(self, devices):
        self.devices = self._normalize_devices(devices)
        self._refresh_device_table()

    def _on_models_loaded(self, models):
        self.device_models = models

    def _on_operation_finished(self, success, msg):
        if success:
            QMessageBox.information(self, "成功", msg)
            self.vm.load_devices()
        else:
            QMessageBox.warning(self, "失败", msg)

    def _on_device_actions_loaded(self, device_id, actions):
        if not isinstance(self._pending_edit_device, dict):
            return
        if self._pending_edit_device.get("id") != device_id:
            return

        device_data = dict(self._pending_edit_device)
        device_data["actions"] = actions if isinstance(actions, list) else []
        self._pending_edit_device = None

        dialog = DeviceDialog(mode="edit", device_data=device_data, models=self.device_models, parent=self)
        if dialog.exec():
            data = dialog.get_data()
            self.vm.update_device(device_id, data)

    def _format_device_status(self, status_value):
        status_map = {0: "离线", 1: "在线", 2: "运行中", 3: "故障"}
        try:
            return status_map.get(int(status_value), "未知")
        except (TypeError, ValueError):
            return "未知"

    def _refresh_device_table(self):
        self.device_table.setRowCount(0)
        for device in self.devices:
            row = self.device_table.rowCount()
            self.device_table.insertRow(row)
            row_values = [
                device.get("device_code", "") or "",
                device.get("device_name", "") or "",
                device.get("device_category", "") or "",
                self._format_device_status(device.get("device_status")),
            ]
            for col, value in enumerate(row_values):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.device_table.setItem(row, col, item)

            actions_container = QWidget()
            actions_layout = QHBoxLayout(actions_container)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(10)
            actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            edit_btn = QPushButton("编辑")
            edit_btn.setFixedSize(80, 36)
            edit_btn.setStyleSheet(
                """
                QPushButton {
                    background-color: #007AFF;
                    color: white;
                    border-radius: 4px;
                    border: none;
                    font-size: 16px;
                }
                QPushButton:pressed { background-color: #0056b3; }
                """
            )
            edit_btn.clicked.connect(lambda checked, d=device: self._on_edit_device_clicked(d))
            actions_layout.addWidget(edit_btn)

            delete_btn = QPushButton("删除")
            delete_btn.setFixedSize(80, 36)
            delete_btn.setStyleSheet(
                """
                QPushButton {
                    background-color: #FF3B30;
                    color: white;
                    border-radius: 4px;
                    border: none;
                    font-size: 16px;
                }
                QPushButton:pressed { background-color: #c42d25; }
                """
            )
            delete_btn.clicked.connect(lambda checked, d=device: self._on_delete_device_clicked(d))
            actions_layout.addWidget(delete_btn)
            self.device_table.setCellWidget(row, 4, actions_container)

    def _on_add_device_clicked(self):
        if not self.device_models:
            QMessageBox.warning(self, "错误", "暂无可用设备型号")
            return
        dialog = DeviceDialog(mode="add", models=self.device_models, parent=self)
        if dialog.exec():
            data = dialog.get_data()
            self.vm.add_device(data)

    def _on_edit_device_clicked(self, device):
        if not isinstance(device, dict) or "id" not in device:
            QMessageBox.warning(self, "错误", "设备数据无效，无法编辑")
            return
        self._pending_edit_device = device
        self.vm.load_device_actions(device["id"])

    def _on_delete_device_clicked(self, device):
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除设备 '{device['device_name']}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.vm.delete_device(device["id"])

    def _create_process_config_view(self):
        container = QFrame()
        container.setStyleSheet("background-color: rgba(255, 255, 255, 0.05); border-radius: 16px;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)

        title = QLabel("工艺配置 & 系统设置")
        title.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

        pwd_section = QFrame()
        pwd_section.setStyleSheet(
            "background-color: rgba(255, 255, 255, 0.03); border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.1);"
        )
        pwd_layout = QVBoxLayout(pwd_section)
        pwd_layout.setContentsMargins(25, 25, 25, 25)
        pwd_layout.setSpacing(20)

        pwd_title = QLabel("修改运维管理密码")
        pwd_title.setStyleSheet("color: white; font-size: 18px; font-weight: bold; border: none;")
        pwd_layout.addWidget(pwd_title)

        form_layout = QGridLayout()
        form_layout.setSpacing(15)
        form_layout.addWidget(QLabel("新密码:"), 0, 0)
        self.new_pwd_input = QLineEdit()
        self.new_pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_pwd_input.setPlaceholderText("请输入新 6 位数字密码")
        self.new_pwd_input.setFixedSize(300, 44)
        self.new_pwd_input.setStyleSheet("background-color: #0B0E14; color: white; border: 1px solid #2A3038; border-radius: 8px; padding-left: 10px;")
        form_layout.addWidget(self.new_pwd_input, 0, 1)

        form_layout.addWidget(QLabel("确认新密码:"), 1, 0)
        self.confirm_pwd_input = QLineEdit()
        self.confirm_pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_pwd_input.setPlaceholderText("请再次输入新密码")
        self.confirm_pwd_input.setFixedSize(300, 44)
        self.confirm_pwd_input.setStyleSheet("background-color: #0B0E14; color: white; border: 1px solid #2A3038; border-radius: 8px; padding-left: 10px;")
        form_layout.addWidget(self.confirm_pwd_input, 1, 1)
        pwd_layout.addLayout(form_layout)

        save_pwd_btn = QPushButton("保存新密码")
        save_pwd_btn.setFixedSize(120, 44)
        save_pwd_btn.setStyleSheet("background-color: #1890ff; color: white; border-radius: 8px; font-weight: bold;")
        save_pwd_btn.clicked.connect(self._save_new_password)
        pwd_layout.addWidget(save_pwd_btn, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addWidget(pwd_section)
        layout.addStretch()
        return container

    def _save_new_password(self):
        new_pwd = self.new_pwd_input.text()
        confirm_pwd = self.confirm_pwd_input.text()
        if not new_pwd or len(new_pwd) < 6:
            QMessageBox.warning(self, "错误", "密码长度至少为 6 位")
            return
        if new_pwd != confirm_pwd:
            QMessageBox.warning(self, "错误", "两次输入的密码不一致")
            return
        config_manager.set("admin_password", new_pwd)
        QMessageBox.information(self, "成功", "密码修改成功！")
        self.new_pwd_input.clear()
        self.confirm_pwd_input.clear()

    def _update_time(self):
        self.time_label.setText(QDateTime.currentDateTime().toString("yyyy/M/d  HH:mm:ss"))
