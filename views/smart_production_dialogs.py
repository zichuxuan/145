import copy
from functools import partial
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QScrollArea,
    QWidget,
    QHBoxLayout,
    QPushButton,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QSpinBox,
    QDialogButtonBox,
    QFrame,
)
from .smart_production_constants import (
    GROUP_ORDER,
    NODE_LIBRARY,
    NODE_SCHEMAS,
    JUDGMENT_PROPERTY_OPTIONS,
    JUDGMENT_OPERATOR_OPTIONS,
    JUDGMENT_LOGIC_OPTIONS,
)
from .smart_production_utils import (
    get_node_label,
    build_default_config,
)

class WorkflowNodePickerDialog(QDialog):
    """工作流节点类型选择弹窗。

    该弹窗用于在远程控制画布中添加新节点时，提供按分组分类的节点选项供用户选择。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_type = None
        self.setWindowTitle("选择节点")
        self.setModal(True)
        self.setFixedSize(900, 760)
        self.setStyleSheet(
            """
            QDialog { background-color: #1C212B; color: white; border: 1px solid rgba(255,255,255,0.15); border-radius: 16px; }
            QLabel { color: white; }
            QPushButton#nodeOption {
                background-color: rgba(255,255,255,0.1);
                color: white;
                border: 1px solid rgba(255,255,255,0.15);
                border-radius: 28px;
                font-size: 22px;
                padding: 14px 28px;
                text-align: center;
            }
            QPushButton#nodeOption:hover { background-color: rgba(255,255,255,0.16); }
            QPushButton#nodeOption:pressed { background-color: rgba(255,255,255,0.22); }
            """
        )
        self._init_ui()

    def _init_ui(self):
        """初始化节点选择弹窗的 UI。
        
        通过滚动区域和分组结构，按照 GROUP_ORDER 动态生成每种类型节点的按钮。
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(22)

        title = QLabel("节点类型")
        title.setStyleSheet("font-size: 34px; font-weight: 600;")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent;")
        content = QWidget()
        scroll_layout = QVBoxLayout(content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(26)

        grouped = {group: [] for group in GROUP_ORDER}
        for node_type, meta in NODE_LIBRARY.items():
            grouped.setdefault(meta["group"], []).append((node_type, meta))

        for group in GROUP_ORDER:
            items = grouped.get(group, [])
            if not items:
                continue
            group_label = QLabel(group)
            group_label.setStyleSheet("font-size: 28px; font-weight: 600;")
            scroll_layout.addWidget(group_label)

            # 每行最多显示 3 个节点
            MAX_PER_ROW = 3
            for i in range(0, len(items), MAX_PER_ROW):
                row_items = items[i : i + MAX_PER_ROW]
                row_widget = QWidget()
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.setSpacing(18)
                row_layout.addStretch()
                for node_type, meta in row_items:
                    btn = QPushButton(meta["label"])
                    btn.setObjectName("nodeOption")
                    btn.setMinimumWidth(180)
                    btn.clicked.connect(partial(self._select_type, node_type))
                    row_layout.addWidget(btn)
                row_layout.addStretch()
                scroll_layout.addWidget(row_widget)

        scroll_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _select_type(self, node_type):
        self.selected_type = node_type
        self.accept()


class WorkflowNodeConfigDialog(QDialog):
    """节点详细配置表单弹窗。

    基于 NODE_SCHEMAS 为不同的节点类型动态生成表单字段，
    并在确认时通过 get_config() 返回收集到的配置字典。
    """
    def __init__(self, node_type, node_config=None, parent=None):
        super().__init__(parent)
        self.node_type = node_type
        self.node_config = copy.deepcopy(node_config or build_default_config(node_type))
        self.widgets = {}
        self.setWindowTitle(f"配置{get_node_label(node_type)}")
        self.setModal(True)
        self.resize(560, 720)
        self.setStyleSheet(
            """
            QDialog { background-color: #1C212B; color: white; border: 1px solid rgba(255,255,255,0.15); border-radius: 16px; }
            QLabel { color: white; font-size: 18px; }
            QLineEdit, QTextEdit, QComboBox, QSpinBox {
                background-color: rgba(255,255,255,0.08);
                color: white;
                border: 1px solid rgba(255,255,255,0.18);
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 18px;
            }
            QComboBox QAbstractItemView {
                background-color: #1F2937;
                color: white;
                selection-background-color: #007AFF;
            }
            QDialogButtonBox QPushButton {
                min-width: 120px;
                min-height: 46px;
                border-radius: 12px;
                font-size: 18px;
            }
            """
        )
        self._init_ui()

    def _init_ui(self):
        """初始化配置表单的基础布局。
        
        如果是判断节点则调用专用的 _init_judgment_ui，
        其他节点通过 QFormLayout 基于 NODE_SCHEMAS 循环构建表单行。
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(20)

        title_text = "判断" if self.node_type == "judgment" else get_node_label(self.node_type)
        title = QLabel(title_text)
        title.setStyleSheet("font-size: 32px; font-weight: 600;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter if self.node_type == "judgment" else Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(title)

        if self.node_type == "judgment":
            self._init_judgment_ui(layout)
        else:
            form_layout = QFormLayout()
            form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
            form_layout.setFormAlignment(Qt.AlignmentFlag.AlignTop)
            form_layout.setHorizontalSpacing(18)
            form_layout.setVerticalSpacing(18)

            for field in NODE_SCHEMAS.get(self.node_type, []):
                widget = self._create_field_widget(field)
                self.widgets[field["key"]] = widget
                form_layout.addRow(field["label"], widget)

            if not self.widgets:
                empty = QLabel("该节点当前没有可配置项")
                empty.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 18px;")
                layout.addWidget(empty)
            else:
                layout.addLayout(form_layout)

        layout.addStretch()

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_button = QPushButton("取消")
        cancel_button.setFixedSize(120, 46)
        cancel_button.setStyleSheet("background-color: rgba(255,255,255,0.08); color: white; border: 1px solid rgba(255,255,255,0.18); border-radius: 12px; font-size: 18px;")

        ok_button = QPushButton("确认")
        ok_button.setFixedSize(120, 46)
        ok_button.setStyleSheet("background-color: #007AFF; color: white; border: none; border-radius: 12px; font-size: 18px;")

        cancel_button.clicked.connect(self.reject)
        ok_button.clicked.connect(self.accept)

        button_layout.addWidget(cancel_button)
        button_layout.addSpacing(16)
        button_layout.addWidget(ok_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)

    def _init_judgment_ui(self, layout):
        """专门为判断节点初始化的定制 UI。
        
        包含 "如果" 和 "否则" 两个分支卡片，并在 "如果" 中包含多行条件编辑。
        """
        layout.addWidget(self._create_section_label("条件分支"))

        if_card = QFrame()
        if_card.setStyleSheet(
            """
            QFrame {
                background-color: rgba(255,255,255,0.04);
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 12px;
            }
            """
        )
        if_layout = QVBoxLayout(if_card)
        if_layout.setContentsMargins(18, 16, 18, 16)
        if_layout.setSpacing(14)

        if_header_row = QHBoxLayout()
        if_header_row.setSpacing(12)
        if_label = QLabel("如果")
        if_label.setStyleSheet("font-size: 20px; font-weight: 600; border: none; background: transparent;")
        if_header_row.addWidget(if_label)
        
        if_header_row.addStretch()
        
        self.add_condition_btn = QPushButton("增加条件")
        self.add_condition_btn.setFixedHeight(36)
        self.add_condition_btn.setStyleSheet(
            "background-color: transparent; color: #60A5FA; border-radius: 6px; border: 1px solid #60A5FA; padding: 0 12px; font-size: 16px;"
        )
        self.add_condition_btn.clicked.connect(self._add_judgment_condition_row)
        if_header_row.addWidget(self.add_condition_btn)
        if_layout.addLayout(if_header_row)

        self.judgment_conditions_layout = QVBoxLayout()
        self.judgment_conditions_layout.setContentsMargins(0, 0, 0, 0)
        self.judgment_conditions_layout.setSpacing(10)
        if_layout.addLayout(self.judgment_conditions_layout)
        
        layout.addWidget(if_card)

        else_card = QFrame()
        else_card.setStyleSheet(
            """
            QFrame {
                background-color: rgba(255,255,255,0.04);
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 12px;
            }
            """
        )
        else_layout = QVBoxLayout(else_card)
        else_layout.setContentsMargins(18, 16, 18, 16)
        
        else_label = QLabel("否则")
        else_label.setStyleSheet("font-size: 20px; font-weight: 600; border: none; background: transparent;")
        else_layout.addWidget(else_label)
        
        layout.addWidget(else_card)

        self.judgment_condition_rows = []
        for rule in self._get_judgment_rules():
            self._add_judgment_condition_row(rule)
        if not self.judgment_condition_rows:
            self._add_judgment_condition_row()

    def _create_section_label(self, text):
        label = QLabel(text)
        label.setStyleSheet("font-size: 20px; font-weight: 600;")
        return label

    def _get_judgment_rules(self):
        rules = self.node_config.get("condition_rules")
        if isinstance(rules, list) and rules:
            return [rule for rule in rules if isinstance(rule, dict)]
        expression = str(self.node_config.get("condition_expression") or "").strip()
        if expression:
            return [{"attribute": JUDGMENT_PROPERTY_OPTIONS[0], "operator": JUDGMENT_OPERATOR_OPTIONS[0], "value": expression, "joiner": "且"}]
        return []

    def _add_judgment_condition_row(self, rule=None):
        """向“如果”分支卡片中添加一行条件编辑。
        
        每行包含属性、操作符、输入值和删除按钮，
        多行时通过刷新机制（_refresh_judgment_condition_rows）处理逻辑下拉框和删除按钮的显示。
        """
        row_frame = QFrame()
        row_frame.setStyleSheet("QFrame { background: transparent; border: none; }")
        row_layout = QVBoxLayout(row_frame)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(12)

        fields_row = QHBoxLayout()
        fields_row.setContentsMargins(0, 0, 0, 0)
        fields_row.setSpacing(10)

        attr_combo = QComboBox()
        for option in JUDGMENT_PROPERTY_OPTIONS:
            attr_combo.addItem(option, option)
        attr_combo.setCurrentText(str((rule or {}).get("attribute") or JUDGMENT_PROPERTY_OPTIONS[0]))
        fields_row.addWidget(attr_combo, 2)

        operator_combo = QComboBox()
        for option in JUDGMENT_OPERATOR_OPTIONS:
            operator_combo.addItem(option, option)
        operator_combo.setCurrentText(str((rule or {}).get("operator") or JUDGMENT_OPERATOR_OPTIONS[0]))
        fields_row.addWidget(operator_combo, 2)

        value_input = QLineEdit()
        value_input.setPlaceholderText("请输入")
        value_input.setText(str((rule or {}).get("value") or ""))
        fields_row.addWidget(value_input, 3)

        delete_btn = QPushButton("删除")
        delete_btn.setFixedSize(60, 40)
        delete_btn.setStyleSheet(
            "background-color: rgba(239,68,68,0.12); color: #F87171; border-radius: 8px; border: 1px solid rgba(239,68,68,0.24); font-size: 16px;"
        )
        delete_btn.setVisible(False)
        fields_row.addWidget(delete_btn)
        
        row_layout.addLayout(fields_row)

        logic_combo = QComboBox()
        for option in JUDGMENT_LOGIC_OPTIONS:
            logic_combo.addItem(option, option)
        logic_combo.setFixedWidth(100)
        logic_combo.setCurrentText(str((rule or {}).get("joiner") or JUDGMENT_LOGIC_OPTIONS[0]))
        row_layout.addWidget(logic_combo, alignment=Qt.AlignmentFlag.AlignLeft)

        row_data = {
            "frame": row_frame,
            "attribute": attr_combo,
            "operator": operator_combo,
            "value": value_input,
            "joiner": logic_combo,
            "delete": delete_btn,
        }
        delete_btn.clicked.connect(partial(self._remove_judgment_condition_row, row_data))
        self.judgment_condition_rows.append(row_data)
        self.judgment_conditions_layout.addWidget(row_frame)
        self._refresh_judgment_condition_rows()

    def _remove_judgment_condition_row(self, row_data):
        if row_data not in self.judgment_condition_rows:
            return
        self.judgment_condition_rows.remove(row_data)
        row_data["frame"].deleteLater()
        if not self.judgment_condition_rows:
            self._add_judgment_condition_row()
            return
        self._refresh_judgment_condition_rows()

    def _refresh_judgment_condition_rows(self):
        """刷新判断节点中各个条件行的状态。
        
        仅当行数 > 1 时显示删除按钮，同时最后一行隐藏逻辑（且/或）下拉框。
        """
        row_count = len(self.judgment_condition_rows)
        for index, row in enumerate(self.judgment_condition_rows):
            row["joiner"].setVisible(index < row_count - 1)
            row["delete"].setVisible(row_count > 1)

    def _collect_judgment_rules(self):
        rules = []
        for row in self.judgment_condition_rows:
            value = row["value"].text().strip()
            if not value:
                continue
            rules.append(
                {
                    "attribute": row["attribute"].currentData() or row["attribute"].currentText().strip(),
                    "operator": row["operator"].currentData() or row["operator"].currentText().strip(),
                    "value": value,
                    "joiner": row["joiner"].currentData() or row["joiner"].currentText().strip(),
                }
            )
        return rules

    def _format_judgment_expression(self, rules):
        parts = []
        for index, rule in enumerate(rules):
            text = f"{rule.get('attribute', '')} {rule.get('operator', '')} {rule.get('value', '')}".strip()
            if not text:
                continue
            parts.append(text)
            if index < len(rules) - 1:
                parts.append(str(rule.get("joiner") or JUDGMENT_LOGIC_OPTIONS[0]))
        return " ".join(parts).strip()

    def _create_field_widget(self, field):
        field_type = field.get("type")
        value = self.node_config.get(field["key"], field.get("default"))
        if field_type == "textarea":
            widget = QTextEdit()
            widget.setMinimumHeight(180)
            widget.setPlainText(str(value or ""))
            return widget
        if field_type == "select":
            widget = QComboBox()
            for option in field.get("options", []):
                widget.addItem(str(option), option)
            index = widget.findData(value)
            if index < 0:
                index = widget.findText(str(value))
            widget.setCurrentIndex(index if index >= 0 else 0)
            return widget
        if field_type == "number":
            widget = QSpinBox()
            widget.setRange(field.get("min", 0), field.get("max", 99999))
            widget.setValue(int(value or field.get("default", 0)))
            return widget
        widget = QLineEdit()
        widget.setText(str(value or ""))
        return widget

    def get_config(self):
        """收集表单中的数据，并返回为字典。
        
        对判断节点执行特殊的字段收集（合并条件为表达式等），
        对其他节点按 NODE_SCHEMAS 获取对应的 QWidget 内容。
        
        Returns:
            dict: 收集并格式化后的配置字典。
        """
        if self.node_type == "judgment":
            result = copy.deepcopy(self.node_config)
            result["condition_name"] = "判断节点"
            result["yes_label"] = "当满足时"
            result["no_label"] = "否则"
            result["condition_rules"] = self._collect_judgment_rules()
            result["condition_expression"] = self._format_judgment_expression(result["condition_rules"])
            return result
        result = copy.deepcopy(self.node_config)
        for field in NODE_SCHEMAS.get(self.node_type, []):
            key = field["key"]
            widget = self.widgets.get(key)
            if isinstance(widget, QTextEdit):
                result[key] = widget.toPlainText().strip()
            elif isinstance(widget, QComboBox):
                result[key] = widget.currentData() or widget.currentText().strip()
            elif isinstance(widget, QSpinBox):
                result[key] = int(widget.value())
            elif isinstance(widget, QLineEdit):
                result[key] = widget.text().strip()
        return result
