# Production Overview Components Design Plan

## 1. Summary
Refine the `ProcessCard`, `SmartStageCard`, and flow connection canvases (`ProductionFlowCanvas1` to `4`) in `/workspace/views/production_overview.py` to match the project's "Material Dark" aesthetic. The changes will make the UI look more exquisite with deep gradients, glowing borders on selection, drop shadows, and smoother connection lines, without changing any text or node positions.

## 2. Proposed Changes

### 2.1 Update Imports
- **File**: `/workspace/views/production_overview.py`
- **Change**: Add `QGraphicsDropShadowEffect` to the PyQt6 imports to enable soft drop shadows.

### 2.2 Refine `ProcessCard` (Lines 97-204)
- **File**: `/workspace/views/production_overview.py`
- **Change**:
  - Add a `QGraphicsDropShadowEffect` to the main frame for depth (blur radius 20, color `rgba(0,0,0,80)`, offset `(0, 6)`).
  - Update `self.setStyleSheet` to use a `qlineargradient` for the background (from `#252A34` to `#1B1E26`) and set a border `#3A4454` with a 16px radius.
  - Refine the `icon_label` background style to have a subtle white border `border: 2px solid rgba(255, 255, 255, 0.15)` along with the accent color.
  - Update `set_status` capsule styling: Use 10% opacity for the background and 30% opacity for the border. Update padding and font weight.
  - Update `self.dot_l` and `self.dot_r` styling to look like glowing nodes: `background-color: #0A84FF; border: 2px solid #1B1E26;`.

### 2.3 Refine `SmartStageCard` (Lines 206-293)
- **File**: `/workspace/views/production_overview.py`
- **Change**:
  - Add a `QGraphicsDropShadowEffect` to the main frame.
  - Update `_apply_selected_style`:
    - **Selected State**: Use a glowing border approach. `background-color: rgba(10, 132, 255, 0.08); border: 2px solid #0A84FF; border-radius: 12px;`
    - **Unselected State**: Use a subtle dark gradient. `background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #252A34, stop:1 #1B1E26); border: 1px solid #3A4454;` with a slightly lighter hover effect.
  - Update `set_running` status capsule styling with better colors and borders (e.g., `#00D084` text, `rgba(0, 208, 132, 0.15)` bg).

### 2.4 Refine Connection Lines in Canvases (Lines 296-770)
- **File**: `/workspace/views/production_overview.py`
- **Change**:
  - In `paintEvent` of `ProductionFlowCanvas1`, `ProductionFlowCanvas2`, `ProductionFlowCanvas3`, and `ProductionFlowCanvas4`:
    - Update `QPen` configuration to create smoother solid lines: `pen = QPen(QColor("#0A84FF"), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)`.
    - Verify that `painter.setRenderHint(QPainter.RenderHint.Antialiasing)` is applied.

## 3. Assumptions & Decisions
- Text, layout structure, and physical positions of all components and lines will remain exactly the same as per user instruction.
- The modifications are strictly CSS (QSS) changes and `QPainter` parameter updates to achieve the "Material Dark" and "Glowing Border" styles.

## 4. Verification
- Open the application and navigate to the Production Overview page.
- Verify that `ProcessCard`s have depth, smooth gradients, and refined status capsules.
- Verify that clicking a `SmartStageCard` highlights it with a glowing blue border.
- Verify that workflow connection lines are smooth, anti-aliased, and rounded.