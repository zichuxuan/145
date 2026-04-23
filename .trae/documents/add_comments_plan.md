# 视图层代码注释补全实现计划

**Goal:** 为 `views` 目录下的核心文件（包括主窗口、总览页、智能生产主页、画布、对话框及相关工具常量）添加全面且规范的中文注释。采用标准的文档字符串（Docstring）格式描述类与方法，并在复杂的业务逻辑和 UI 渲染代码中添加行内注释，以提高代码可读性和可维护性。

**Architecture:** 
- 不改变任何现有业务逻辑、数据流或 UI 布局。
- 采用标准的 Google/Sphinx 风格为类和函数编写 Docstring（包含功能描述、Args、Returns 等）。
- 针对画布缩放、节点递归渲染、分支条件动态增删等复杂操作增加详细的行内注释。

**Tech Stack:** PyQt6, Python (Docstrings)

---

## 现状分析 (Current State Analysis)
- `main_window.py` 和 `production_overview.py` 已包含部分模块级和类级的自然语言注释，但不够规范，且缺少方法参数和返回值的标准说明。
- `smart_production_canvas.py` 包含了复杂的基于布局的节点渲染（如缩放换算、递归绘制分支）、组件动态装卸（如全屏切换），目前完全缺乏注释，理解成本较高。
- `smart_production.py` 承担了大量与 ViewModel 和 Service 通信的职责，以及页面间的状态流转，相关生命周期缺乏说明。
- `smart_production_dialogs.py` 中判断节点条件的动态增删、数据收集逻辑较为复杂，需要补充行内注释。
- 常量文件 `smart_production_constants.py` 缺乏对节点类型和结构约定的整体说明。

---

## Proposed Changes (具体实施步骤)

### Task 1: 补充基础与公共模块注释
**Files:**
- Modify: `/workspace/views/smart_production_constants.py`
- Modify: `/workspace/views/smart_production_utils.py`

**内容说明:**
1. **常量文件**: 在文件头部添加模块注释，解释该文件的作用（存放节点库、配置 Schema、设备类型及下拉选项等），并为 `NODE_LIBRARY` 和 `NODE_SCHEMAS` 添加详细的结构说明（如键值对的含义）。
2. **工具文件**: 为 `clear_layout`, `create_node`, `create_default_workflow_detail`, `get_node_summary` 等工具函数补充标准 Docstring，说明入参（如 `node_type`, `workflow`）的结构和返回值。

### Task 2: 补充对话框与表单逻辑注释
**Files:**
- Modify: `/workspace/views/smart_production_dialogs.py`

**内容说明:**
1. 为 `WorkflowNodePickerDialog` 和 `WorkflowNodeConfigDialog` 类添加标准 Docstring，解释其承担的用户交互职责。
2. 为 `_init_ui` 和 `_init_judgment_ui` 方法添加注释，说明 UI 组件树的构建层级。
3. 在 `_add_judgment_condition_row`、`_remove_judgment_condition_row` 和 `_refresh_judgment_condition_rows` 方法中添加行内注释，解释动态条件行（包含属性、运算符、值、逻辑连接符及删除按钮）的增删与状态刷新逻辑。
4. 为 `get_config` 和 `_collect_judgment_rules` 添加说明，阐述从 UI 控件中提取和规范化节点数据的过程。

### Task 3: 补充核心工作流画布注释
**Files:**
- Modify: `/workspace/views/smart_production_canvas.py`

**内容说明:**
1. 为 `ElseBranchEndSection` 和 `WorkflowCanvasEditor` 类添加整体 Docstring。
2. 在缩放控制（`set_zoom_factor`, `_scaled`）中添加行内注释，解释基于乘数动态计算像素大小以实现布局缩放的原理。
3. 为 `_build_sequence_widget`, `_create_branching_node`, `_create_loop_node` 等方法添加详细注释，解释工作流数据如何从 `sequence` 列表递归映射为嵌套的 `QFrame` 和 `QHBoxLayout/QVBoxLayout`。
4. 为节点交互（`_add_node`, `_edit_node`, `_delete_node`）增加行内注释，说明对 `sequence` 数据结构的修改及其如何触发 `render_canvas` 重新渲染。

### Task 4: 补充智能生产主页面与交互桥梁注释
**Files:**
- Modify: `/workspace/views/smart_production.py`

**内容说明:**
1. 为 `SmartProduction` 类添加 Docstring，说明其作为智能生产管理（基本配置与远程控制/画布）主容器的作用。
2. 为加载与保存流程的生命周期方法（`_open_edit_workflow`, `_on_workflow_detail_loaded`, `_collect_workflow_payload`, `_submit_workflow`）添加注释，明确其与 `DeviceViewModel` 之间的异步交互和信号槽绑定机制。
3. 对全屏模式切换逻辑（`_enter_workflow_canvas_fullscreen`, `_attach_workflow_canvas_editor`）增加行内说明，解释 `setParent(None)` 转移 Widget 所解决的问题。

### Task 5: 补充全局总览与主窗口注释
**Files:**
- Modify: `/workspace/views/main_window.py`
- Modify: `/workspace/views/production_overview.py`

**内容说明:**
1. 规范 `MainWindow` 和 `ProductionOverview` 现有的简短注释，升级为包含标准块的 Docstring。
2. 为 `ProductionOverview` 中的事件过滤器 `eventFilter` 补充关于“Logo 连续点击 3 次触发隐藏入口”这一安全/运维机制的行内逻辑注释。
3. 为 `StatusCard` 类以及定时器 `QTimer` 的使用添加说明。

---

## Assumptions & Decisions (假设与决策)
- **非侵入性**: 注释添加过程严格保证不更改任何执行代码、变量命名或缩进层级（除注释占用的新行外）。
- **语言一致性**: 统一使用中文（简体）进行说明。
- **标准约定**: 采用 Google 风格的 Docstring 格式，即 `Args:` 和 `Returns:` 结构。

## Verification (验证步骤)
1. 运行 `python -m py_compile <file>` 确保增加注释后所有修改过的文件没有引发语法错误（如缩进异常）。
2. （可选）使用 `pydocstyle` 或在 IDE 中查看悬浮提示，确认 Docstring 的解析效果良好。
3. 运行项目入口 `main.py`，确认系统正常启动，各个页面及工作流画布渲染未因排版变动受到影响。