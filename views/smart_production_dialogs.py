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
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(20)

        title = QLabel(get_node_label(self.node_type))
        title.setStyleSheet("font-size: 32px; font-weight: 600;")
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

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        cancel_button = button_box.button(QDialogButtonBox.StandardButton.Cancel)
        if ok_button:
            ok_button.setText("确认")
            ok_button.setStyleSheet("background-color: #007AFF; color: white; border: none;")
        if cancel_button:
            cancel_button.setText("取消")
            cancel_button.setStyleSheet("background-color: rgba(255,255,255,0.08); color: white; border: 1px solid rgba(255,255,255,0.18);")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _init_judgment_ui(self, layout):
        self.widgets["condition_name"] = QLineEdit()
        self.widgets["condition_name"].setText(str(self.node_config.get("condition_name") or "判断节点"))
        layout.addWidget(self._create_section_label("判断名称"))
        layout.addWidget(self.widgets["condition_name"])

        layout.addWidget(self._create_section_label("条件分支"))

        branch_card = QFrame()
        branch_card.setStyleSheet(
            """
            QFrame {
                background-color: rgba(255,255,255,0.04);
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 12px;
            }
            """
        )
        card_layout = QVBoxLayout(branch_card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(14)

        if_row = QHBoxLayout()
        if_row.setSpacing(12)
        if_label = QLabel("如果")
        if_label.setStyleSheet("font-size: 20px; font-weight: 600;")
        if_row.addWidget(if_label)
        self.widgets["yes_label"] = QLineEdit()
        self.widgets["yes_label"].setPlaceholderText("满足条件时分支文案")
        self.widgets["yes_label"].setText(str(self.node_config.get("yes_label") or "当满足时"))
        if_row.addWidget(self.widgets["yes_label"], stretch=1)
        self.add_condition_btn = QPushButton("增加条件")
        self.add_condition_btn.setFixedHeight(40)
        self.add_condition_btn.setStyleSheet(
            "background-color: rgba(0,122,255,0.15); color: #60A5FA; border-radius: 8px; border: 1px solid rgba(96,165,250,0.45);"
        )
        self.add_condition_btn.clicked.connect(self._add_judgment_condition_row)
        if_row.addWidget(self.add_condition_btn)
        card_layout.addLayout(if_row)

        self.judgment_conditions_layout = QVBoxLayout()
        self.judgment_conditions_layout.setContentsMargins(0, 0, 0, 0)
        self.judgment_conditions_layout.setSpacing(10)
        card_layout.addLayout(self.judgment_conditions_layout)

        else_label = QLabel("否则")
        else_label.setStyleSheet("font-size: 20px; font-weight: 600;")
        card_layout.addWidget(else_label)

        self.widgets["no_label"] = QLineEdit()
        self.widgets["no_label"].setPlaceholderText("否则分支文案")
        self.widgets["no_label"].setText(str(self.node_config.get("no_label") or "否则"))
        card_layout.addWidget(self.widgets["no_label"])
        layout.addWidget(branch_card)

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
        row_frame = QFrame()
        row_frame.setStyleSheet("QFrame { background: transparent; border: none; }")
        row_layout = QVBoxLayout(row_frame)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)

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

        delete_btn = QPushButton("删")
        delete_btn.setFixedSize(40, 40)
        delete_btn.setStyleSheet(
            "background-color: rgba(239,68,68,0.12); color: #F87171; border-radius: 8px; border: 1px solid rgba(239,68,68,0.24);"
        )
        fields_row.addWidget(delete_btn)
        row_layout.addLayout(fields_row)

        logic_combo = QComboBox()
        for option in JUDGMENT_LOGIC_OPTIONS:
            logic_combo.addItem(option, option)
        logic_combo.setFixedWidth(120)
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
        row_count = len(self.judgment_condition_rows)
        for index, row in enumerate(self.judgment_condition_rows):
            row["joiner"].setVisible(index < row_count - 1)
            row["delete"].setEnabled(row_count > 1)

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
        if self.node_type == "judgment":
            result = copy.deepcopy(self.node_config)
            result["condition_name"] = self.widgets["condition_name"].text().strip() or "判断节点"
            result["yes_label"] = self.widgets["yes_label"].text().strip() or "当满足时"
            result["no_label"] = self.widgets["no_label"].text().strip() or "否则"
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
