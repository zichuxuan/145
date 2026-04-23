# 判断节点配置弹窗重构实现计划

**Goal:** 根据设计方案，重构工作流编辑器中判断节点的配置弹窗布局和字段，精简不必要字段，优化分支展示UI。

**Architecture:** 
- 修改 `WorkflowNodeConfigDialog` 类中的 UI 初始化方法（`_init_ui` 和 `_init_judgment_ui`）。
- 调整 `_add_judgment_condition_row` 中条件行的渲染逻辑。
- 调整 `get_config` 中对判断节点数据的提取，移除被隐藏的输入框依赖。

**Tech Stack:** PyQt6, Python

---

## Task 1: 调整弹窗标题和底部按钮布局
**Files:**
- Modify: `/workspace/views/smart_production_dialogs.py`

- [ ] **Step 1: 修改弹窗标题和底部按钮样式**
在 `WorkflowNodeConfigDialog._init_ui` 方法中：
1. 修改弹窗标题：如果是判断节点，仅显示“判断”，否则保留原本的“配置 xxx”格式。
2. 居中显示底部按钮，并且保持确认按钮和取消按钮的样式。

```python
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(20)

        # 修改弹窗内的标题
        title_text = "判断" if self.node_type == "judgment" else get_node_label(self.node_type)
        title = QLabel(title_text)
        title.setStyleSheet("font-size: 32px; font-weight: 600;")
        # 如果是判断节点，可以让标题居中，不过原代码是左对齐，这里我们保持一致或居中
        title.setAlignment(Qt.AlignmentFlag.AlignCenter if self.node_type == "judgment" else Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(title)

        if self.node_type == "judgment":
            self._init_judgment_ui(layout)
        else:
            # 原有非判断节点的逻辑保持不变
            ...

        layout.addStretch()

        # 修改底部按钮区域为居中
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
```
*(注意：需要替换原本的 `QDialogButtonBox`)*

- [ ] **Step 2: 验证更改**
确保非判断节点的弹窗正常工作，并且底部按钮成功居中显示。

---

## Task 2: 重构 `_init_judgment_ui` (条件分支容器与隐藏字段)
**Files:**
- Modify: `/workspace/views/smart_production_dialogs.py`

- [ ] **Step 1: 重写 `_init_judgment_ui` 方法**
移除 `condition_name`, `yes_label`, `no_label` 的输入框创建。构建两个主要的 Card：“如果”和“否则”。

```python
    def _init_judgment_ui(self, layout):
        layout.addWidget(self._create_section_label("条件分支"))

        # --- “如果” 卡片 ---
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

        # --- “否则” 卡片 ---
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

        # 初始化条件列表
        self.judgment_condition_rows = []
        for rule in self._get_judgment_rules():
            self._add_judgment_condition_row(rule)
        if not self.judgment_condition_rows:
            self._add_judgment_condition_row()
```

- [ ] **Step 2: 检查语法与依赖**
确保去除了旧有的对 `self.widgets["condition_name"]` 等组件的依赖。

---

## Task 3: 重构条件行样式与删除逻辑
**Files:**
- Modify: `/workspace/views/smart_production_dialogs.py`

- [ ] **Step 1: 修改 `_add_judgment_condition_row` 方法**
调整垃圾桶按钮样式（使用文字“🗑️”或红色图标），并将 `logic_combo`（且/或）放置在每行条件的下方（除了最后一行），并且靠左显示。

```python
    def _add_judgment_condition_row(self, rule=None):
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

        delete_btn = QPushButton("🗑️")
        delete_btn.setFixedSize(40, 40)
        delete_btn.setStyleSheet(
            "background-color: transparent; color: #EF4444; border: none; font-size: 20px;"
        )
        # 初始默认隐藏，由 _refresh 控制
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
```

- [ ] **Step 2: 修改 `_refresh_judgment_condition_rows` 方法**
更新条件行刷新逻辑，控制垃圾桶按钮仅在有多行时，且针对第一行隐藏（或者所有行都显示但第一行在仅有一行时隐藏。根据设计，第一行在有多行时也不显示删除，但为方便用户操作，通常允许多行时删除任意行。这里我们实现“只有一行时隐藏删除按钮”）。

```python
    def _refresh_judgment_condition_rows(self):
        row_count = len(self.judgment_condition_rows)
        for index, row in enumerate(self.judgment_condition_rows):
            # 最后一行不显示“且/或”下拉框
            row["joiner"].setVisible(index < row_count - 1)
            # 只有一行时不显示删除按钮
            row["delete"].setVisible(row_count > 1)
```

---

## Task 4: 更新保存逻辑
**Files:**
- Modify: `/workspace/views/smart_production_dialogs.py`

- [ ] **Step 1: 修改 `get_config` 方法**
对于判断节点，直接将硬编码默认值写入配置，替代原有的通过 UI 读取的逻辑。

```python
    def get_config(self):
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
```

- [ ] **Step 2: 验证所有代码更改**
通过测试确保弹窗正常渲染，节点配置成功保存。
