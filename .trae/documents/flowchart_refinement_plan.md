# 生产流程图精修计划

## 1. 目标与范围 (Summary)
对 `/workspace/views/production_overview.py` 中的四个流程图 (`ProductionFlowCanvas1` 到 `ProductionFlowCanvas4`) 进行视觉精修。
**保留项**：不改变任何文字、节点位置、卡片样式和主题色。
**修改项**：
- **Flow Animation (流动动画)**：将连接线修改为带有动画效果的虚线，以表现产线的流动状态。
- **Orthogonal Lines (正交连线)**：将目前的直线和贝塞尔曲线连接替换为带有圆角的正交折线（曼哈顿路由），使工业流程图更加专业。

## 2. 当前状态分析 (Current State Analysis)
- 当前 4 个流程图画布直接继承自 `QWidget`。
- 节点之间的连线在 `paintEvent` 中通过 `painter.drawLine` 和 `curve_path.cubicTo` 绘制。
- 连线为纯实线 `QPen(QColor("#007AFF"), 3)`，缺乏流动感。
- 跨行连线使用了不规则的 S 型贝塞尔曲线，显得不够严谨和工业化。

## 3. 拟修改方案 (Proposed Changes)
**文件**: `/workspace/views/production_overview.py`

**具体步骤**:
1. **创建基础画布类 `BaseFlowCanvas`**:
   - 在 `ProductionFlowCanvas1` 之前定义一个 `BaseFlowCanvas(QWidget)`。
   - 初始化 `QTimer` 用于控制动画偏移量 `self.dash_offset`。
   - 提供公共属性 `base_img_path` 和 `wf_img_path`。
   - 实现通用的获取连接点方法 `_get_node_point(node, side)`。
   - 实现生成正交圆角路径的方法 `_get_orthogonal_path(p1, p2, path_type, offset)`。
   - 实现带流动动画的路径绘制方法 `_draw_animated_path(painter, path)`：绘制一层半透明的实线底色，再绘制一层高亮的虚线（通过设置 `setDashPattern` 和 `setDashOffset`），实现流动效果。

2. **改造现有的 4 个流程图类**:
   - 将继承自 `QWidget` 改为继承自 `BaseFlowCanvas`。
   - 删除各自 `__init__` 中冗余的 `self.base_img_path` 等初始化代码（调用 `super().__init__(parent)` 即可）。
   - 将 `_draw_connection` 和 `_draw_connection_reverse` 统一委托给父类的方法实现。
   - 在各自的 `paintEvent` 中，将跨行连线（如 N4 右到 N8 右，N5 左到 N9 左）的贝塞尔曲线替换为调用 `_get_orthogonal_path(..., type="right_to_right" / "left_to_left")`，并用 `_draw_animated_path` 绘制。

## 4. 假设与决策 (Assumptions & Decisions)
- **动画频率**: `QTimer` 设置为约 50ms 刷新一次，每次 `dash_offset` 减少或增加一定数值。
- **圆角半径**: 正交折线的圆角半径设定为 16px，保持与现有卡片圆角风格一致。
- **重构风险控制**: 核心改动仅限于连线绘制逻辑，不会触碰 `ProcessCard` 或 `CircleMark` 的渲染及布局。

## 5. 验证步骤 (Verification steps)
- 修改完成后，检查 Python 语法是否正确。
- （如有可能）运行该 PyQt6 界面，观察连线是否呈现带有圆角的直角折线，并且虚线是否有持续的流动动画效果。
- 确保所有的节点布局对齐情况与修改前完全一致。