# 节点配置弹窗 QComboBox 样式优化计划

## 1. 概述 (Summary)
优化 `views/smart_production_dialogs.py` 中 `WorkflowNodeConfigDialog` 节点配置弹窗内的 `QComboBox` 样式，解决现有下拉框设计简陋、与现代深色主题 (Dark Theme) 视觉不匹配的问题。

## 2. 当前状态分析 (Current State Analysis)
- **硬编码的 QPalette**: 当前通过 `_apply_combo_dark_style` 方法单独为每一个下拉框强制设置 `QPalette` 的背景色（#2D3748）。
- **粗糙的 QSS**: 弹窗全局 `setStyleSheet` 里面对 `QComboBox` 和 `QComboBox QAbstractItemView` 的设置过于简单，缺少对 Hover、Disabled、Pressed 状态的处理，边框样式生硬。下拉箭头的 `::drop-down` 和 `::down-arrow` 也没有进行现代化的绘制和优化。

## 3. 具体修改方案 (Proposed Changes)

### 3.1 优化 `WorkflowNodeConfigDialog` 的全局 QSS 样式表
修改 `/workspace/views/smart_production_dialogs.py` 中 `WorkflowNodeConfigDialog.__init__` 里的 `setStyleSheet` 字符串：
1. **基础样式 (`QComboBox`)**: 
   - 调整背景色为更通透的 `rgba(255, 255, 255, 0.05)`，与输入框保持一致。
   - 增加边框 `1px solid rgba(255, 255, 255, 0.15)` 并设置圆角 `8px`。
   - 增加悬停状态 (`:hover`) 效果：边框提亮 `rgba(255, 255, 255, 0.3)`。
   - 增加展开状态 (`:on`) 效果：背景色提亮。
   - 增加禁用状态 (`:disabled`) 效果：降低不透明度和修改颜色，避免“加载中”状态过于突兀。
2. **下拉箭头 (`QComboBox::drop-down`)**: 
   - 去除默认的箭头按钮边框和背景，将右侧 Padding 设置合理，并使用现代化的下三角图标或者简单的边框旋转来代替老旧箭头。
   - 设置 `image: none;` 及利用 `border` 绘制一个精美的向下箭头。
3. **下拉列表弹窗 (`QComboBox QAbstractItemView`)**:
   - 设置背景色为深色实色 `#212631`，避免文字重叠。
   - 增加内边距，移除默认的列表边框，设置圆角。
   - 配置选中项 (`::item:selected`) 的背景色为柔和的品牌蓝 `#007AFF` 带有一定透明度，圆角处理。
   - 配置列表项 (`::item`) 的高度和行距，增强可读性。

### 3.2 简化 `_apply_combo_dark_style` 逻辑
为了防止硬编码的 `QPalette` 覆盖我们在 QSS 中精心设计的 `:hover` 和 `:disabled` 颜色，修改该方法：
- 移除手动 `setPalette` 和局部 `setStyleSheet`，完全依赖于 QDialog 统一设置的样式表。该方法可以保留为空或者直接移除。

## 4. 假设与决策 (Assumptions & Decisions)
- **纯 CSS 驱动**: 决定完全使用 Qt Style Sheets (QSS) 来实现所有的视觉效果（包括下拉箭头），而不依赖外部图片文件，这有助于降低资源依赖。
- **暗黑主题风格**: 继续沿用 `#1C212B` 作为弹窗主背景色，下拉框使用半透明的白色层叠加，符合主流的高级管理后台 UI 设计规范。

## 5. 测试验证 (Verification Steps)
1. 在修改完成后，打开任意一个带下拉框的节点配置弹窗（如“螺旋输送机”或“判断”节点）。
2. 检查下拉框的默认状态：是否有圆角、边框、半透明背景。
3. 检查悬浮 (Hover) 状态：鼠标移上去时，边框和背景是否产生亮色反馈。
4. 检查点击展开状态：下拉列表项背景是否为深色，条目间距是否宽松，选中的条目是否有圆角高亮蓝底。
5. 检查禁用状态 (如“加载中...”期间)：文字颜色和背景色是否呈现变暗/变灰的视觉效果。