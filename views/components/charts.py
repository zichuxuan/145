from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QFont

class LineChart(QWidget):
    """产线能耗折线图组件。

    当前数据为静态示例数据，绘制时会根据窗口大小动态换算坐标，
    因而可直接复用于卡片容器中的不同尺寸场景。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = [20, 40, 30, 50, 45, 60, 55]
        self.labels = ["2026/4/10", "2026/4/11", "2026/4/12", "2026/4/13", "2026/4/14", "2026/4/15", "2026/4/16"]
        self.point_color = QColor("#ffffff")
        self.line_gradient_stops = [
            (0.0, QColor("#2AFADF")),
            (0.28, QColor("#00C2FF")),
            (0.58, QColor("#4D6BFF")),
            (0.82, QColor("#8B5CFF")),
            (1.0, QColor("#FF4FD8")),
        ]
        
    def paintEvent(self, event):
        """按当前控件尺寸绘制折线、渐变填充和横轴标签。"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        # padding 用于给折线与标签预留边距，避免贴边。
        padding = 40
        
        # 当前版本不画背景网格，刻意保持更简洁的视觉效果。
        
        if not self.data:
            return
            
        # 纵轴上方额外留 20% 空间，避免最高点顶到边界。
        max_val = max(self.data) * 1.2
        min_val = 0
        
        points = []
        # 横向步进按照数据点数量平均分布。
        x_step = (width - 2 * padding) / (len(self.data) - 1)
        
        for i, val in enumerate(self.data):
            x = padding + i * x_step
            # 将业务值映射到像素坐标系，Qt 左上角为原点，所以 y 值需要反向计算。
            y = height - padding - (val - min_val) / (max_val - min_val) * (height - 2 * padding)
            points.append(QPointF(x, y))
            
        # 折线本身使用横向大跨度渐变，更贴近设计稿的科技感。
        line_gradient = QLinearGradient(padding, 0, width - padding, 0)
        for stop, color in self.line_gradient_stops:
            line_gradient.setColorAt(stop, color)
        pen = QPen(QBrush(line_gradient), 3)
        painter.setPen(pen)
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i+1])

        # 节点使用纯白描边 + 渐变内芯，避免在深色背景上丢失层次。
        for i, point in enumerate(points):
            point_color = self.line_gradient_stops[min(i, len(self.line_gradient_stops) - 1)][1]
            painter.setBrush(QBrush(point_color))
            painter.setPen(QPen(self.point_color, 1.5))
            painter.drawEllipse(point, 4, 4)
            
        # 再绘制折线下方的渐变区域，增强层次感。
        path = [QPointF(padding, height - padding)] + points + [QPointF(width - padding, height - padding)]
        gradient = QLinearGradient(0, 0, 0, height)
        # 面积填充拉大颜色跨度，形成更明显的冷暖过渡。
        gradient.setColorAt(0.0, QColor(255, 79, 216, 88))
        gradient.setColorAt(0.32, QColor(122, 92, 255, 72))
        gradient.setColorAt(0.65, QColor(0, 194, 255, 42))
        gradient.setColorAt(1.0, QColor(42, 250, 223, 0))
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(path)
        
        # 最后绘制横轴日期标签。
        painter.setPen(QColor("#8C8C8C"))
        font = QFont("Inter", 8)
        painter.setFont(font)
        for i, label in enumerate(self.labels):
            x = padding + i * x_step
            rect = QRectF(x - 40, height - padding + 5, 80, 20)
            # 每个标签使用固定宽度矩形居中绘制，保证日期文本对齐。
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, label)

class BarChart(QWidget):
    """生产统计柱状图组件。"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = [50, 80, 40, 30, 20, 35, 60, 70, 55, 90, 110, 75]
        self.labels = ["3A", "绿瓶", "二级蓝白", "杂瓶", "吸塑片", "小油壶", "尾料", "乐虎", "花口瓶", "透明丙", "瓷白", "标签"]
        # 每根柱子都使用大跨度渐变，而不是单一色相的明暗变化。
        self.bar_gradients = [
            ("#2AFADF", "#00C2FF", "#3F87FF"),
            ("#52F1FF", "#1E96FF", "#725CFF"),
            ("#68E0FF", "#4D6BFF", "#9C4DFF"),
            ("#89F7FE", "#6253E1", "#B14BFF"),
            ("#36D1DC", "#5B86E5", "#C85CFF"),
            ("#4FACFE", "#6A5BFF", "#FF5FD2"),
        ]
        
    def paintEvent(self, event):
        """绘制柱状图及底部类目标签。"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        # 底部给标签留空间，两侧给柱子边距。
        padding_bottom = 40
        padding_side = 20
        
        if not self.data:
            return
            
        # 顶部预留少量空间，避免最高柱子顶满。
        max_val = max(self.data) * 1.1
        bar_count = len(self.data)
        # 柱子宽度刻意做窄一些，以更贴近设计稿中的轻盈视觉效果。
        bar_width = (width - 2 * padding_side) / bar_count * 0.4
        spacing = (width - 2 * padding_side) / bar_count
        
        for i, val in enumerate(self.data):
            x = padding_side + i * spacing + (spacing - bar_width) / 2
            # 将业务数值按最大值比例映射为柱高。
            h = (val / max_val) * (height - padding_bottom - 20)
            y = height - padding_bottom - h
            
            rect = QRectF(x, y, bar_width, h)
            top_color, mid_color, bottom_color = [
                QColor(color) for color in self.bar_gradients[i % len(self.bar_gradients)]
            ]
            
            # 每个柱子都采用跨色更大的三段式渐变。
            gradient = QLinearGradient(x, y, x, y + h)
            gradient.setColorAt(0.0, top_color.lighter(112))
            gradient.setColorAt(0.45, mid_color)
            gradient.setColorAt(1.0, bottom_color.darker(118))
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, 4, 4)

            highlight_rect = QRectF(x + 1.5, y + 2, max(bar_width * 0.28, 2), max(h - 5, 0))
            if highlight_rect.height() > 0:
                highlight = QLinearGradient(highlight_rect.x(), 0, highlight_rect.right(), 0)
                highlight.setColorAt(0.0, QColor(255, 255, 255, 70))
                highlight.setColorAt(1.0, QColor(255, 255, 255, 0))
                painter.setBrush(QBrush(highlight))
                painter.drawRoundedRect(highlight_rect, 3, 3)
            
            # 底部类目名称与柱子按同样节奏均匀排列。
            painter.setPen(QColor("#FFFFFF"))
            font = QFont("Inter", 8)
            painter.setFont(font)
            label_rect = QRectF(padding_side + i * spacing, height - padding_bottom + 5, spacing, 20)
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, self.labels[i])

class StorageBar(QWidget):
    """仓储料位条组件。

    通过单个纵向柱形直观展示某个缓存仓当前库存占比。
    """
    def __init__(self, label, value, unit="kg", color="#1890ff", gradient_colors=None, max_value=1000, parent=None):
        super().__init__(parent)
        self.label = label
        self.value = value
        self.unit = unit
        self.color = QColor(color)
        self.gradient_colors = gradient_colors
        # 使用统一标尺换算柱高，保证多个仓储条之间的高度对比准确。
        self.max_value = max(max_value, 1)

    def _get_fill_gradient_stops(self, fill_ratio):
        """返回随柱高变化的渐变色停靠点。"""
        if self.gradient_colors:
            base_top = QColor(self.gradient_colors[0])
            base_bottom = QColor(self.gradient_colors[1])
        elif self.color.name() == "#1890ff":  # 蓝色系仓储条
            base_top = QColor("#1890FF")
            base_bottom = QColor("#0050B3")
        else:  # 橙黄色系仓储条
            base_top = QColor("#FFA940")
            base_bottom = QColor("#D46B08")

        # 高柱子保留更多亮部，低柱子更快过渡到深色，形成“随高度变色”的效果。
        highlight_strength = 100 + int(fill_ratio * 35)
        shadow_strength = 135 - int(fill_ratio * 15)
        mid_stop = max(0.18, 0.42 - fill_ratio * 0.18)

        return [
            (0.0, base_top.lighter(highlight_strength)),
            (mid_stop, base_top),
            (1.0, base_bottom.darker(shadow_strength)),
        ]
        
    def paintEvent(self, event):
        """绘制料位值、背景槽、填充柱、刻度提示和底部标题。"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # 顶部显示当前库存值与单位。
        painter.setPen(QColor("#FFFFFF"))
        painter.setFont(QFont("Inter", 10, QFont.Weight.Bold))
        painter.drawText(QRectF(0, 0, width, 20), Qt.AlignmentFlag.AlignCenter, f"{self.value}{self.unit}")
        
        # 先绘制背景槽，做成更贴近设计稿的暗色玻璃轨道。
        bar_y = 30
        bar_height = height - 70  # 底部留给仓库名称标签。
        bar_width = width * 0.42
        bar_x = (width - bar_width) / 2
        
        bg_rect = QRectF(bar_x, bar_y, bar_width, bar_height)
        track_gradient = QLinearGradient(0, bar_y, 0, bar_y + bar_height)
        track_gradient.setColorAt(0, QColor("#161C24"))
        track_gradient.setColorAt(1, QColor("#262E39"))
        painter.setBrush(QBrush(track_gradient))
        painter.setPen(QPen(QColor(255, 255, 255, 22), 1))
        painter.drawRoundedRect(bg_rect, 8, 8)

        # 轨道内部再叠一层微弱高光，让边缘更像 Figma 里的半透明质感。
        inner_track_rect = bg_rect.adjusted(2, 2, -2, -2)
        inner_track_gradient = QLinearGradient(bar_x, bar_y, bar_x + bar_width, bar_y)
        inner_track_gradient.setColorAt(0, QColor(255, 255, 255, 18))
        inner_track_gradient.setColorAt(0.45, QColor(255, 255, 255, 6))
        inner_track_gradient.setColorAt(1, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(inner_track_gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(inner_track_rect, 7, 7)
        
        # 再绘制填充部分，高度按当前值 / 最大值计算。
        fill_ratio = min(self.value / self.max_value, 1.0)
        fill_height = fill_ratio * inner_track_rect.height()
        fill_rect = QRectF(
            inner_track_rect.x(),
            inner_track_rect.y() + inner_track_rect.height() - fill_height,
            inner_track_rect.width(),
            fill_height,
        )
        
        gradient = QLinearGradient(0, bar_y + bar_height - fill_height, 0, bar_y + bar_height)
        for stop, color in self._get_fill_gradient_stops(fill_ratio):
            gradient.setColorAt(stop, color)
        
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(fill_rect, 7, 7)

        # 顶部高光帽沿，增强“液面”感。
        top_cap_height = min(14, max(6, fill_height * 0.16))
        top_cap_rect = QRectF(fill_rect.x(), fill_rect.y(), fill_rect.width(), top_cap_height)
        top_cap_gradient = QLinearGradient(0, top_cap_rect.y(), 0, top_cap_rect.y() + top_cap_rect.height())
        top_cap_gradient.setColorAt(0, QColor(255, 255, 255, 120))
        top_cap_gradient.setColorAt(1, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(top_cap_gradient))
        painter.drawRoundedRect(top_cap_rect, 7, 7)

        # 左侧纵向反光条，模拟设计稿中的玻璃感。
        sheen_rect = QRectF(fill_rect.x() + 2, fill_rect.y() + 3, fill_rect.width() * 0.32, max(fill_rect.height() - 6, 0))
        if sheen_rect.height() > 0:
            sheen_gradient = QLinearGradient(sheen_rect.x(), 0, sheen_rect.x() + sheen_rect.width(), 0)
            sheen_gradient.setColorAt(0, QColor(255, 255, 255, 76))
            sheen_gradient.setColorAt(1, QColor(255, 255, 255, 0))
            painter.setBrush(QBrush(sheen_gradient))
            painter.drawRoundedRect(sheen_rect, 6, 6)

        # 底部轻微发光，压出悬浮层次。
        glow_rect = QRectF(fill_rect.x(), fill_rect.bottom() - 10, fill_rect.width(), 10)
        glow_gradient = QLinearGradient(0, glow_rect.y(), 0, glow_rect.bottom())
        glow_gradient.setColorAt(0, QColor(255, 255, 255, 0))
        glow_gradient.setColorAt(1, QColor(255, 255, 255, 28))
        painter.setBrush(QBrush(glow_gradient))
        painter.drawRoundedRect(glow_rect, 6, 6)
        
        # 用虚线标出高料位/低料位的参考位置。
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1, Qt.PenStyle.DashLine))
        painter.drawLine(QPointF(bar_x, bar_y + bar_height * 0.25), QPointF(bar_x + bar_width, bar_y + bar_height * 0.25))
        painter.drawLine(QPointF(bar_x, bar_y + bar_height * 0.75), QPointF(bar_x + bar_width, bar_y + bar_height * 0.75))

        # 文本提示辅助操作员快速理解当前料位区间。
        painter.setPen(QColor("#8C8C8C"))
        painter.setFont(QFont("Inter", 8))
        painter.drawText(QRectF(0, bar_y + bar_height * 0.25 - 10, width, 10), Qt.AlignmentFlag.AlignCenter, "高料位")
        painter.drawText(QRectF(0, bar_y + bar_height * 0.75 + 2, width, 10), Qt.AlignmentFlag.AlignCenter, "低料位")
        
        # 底部显示仓库名称。
        painter.setPen(QColor("#FFFFFF"))
        painter.setFont(QFont("Inter", 9))
        painter.drawText(QRectF(0, height - 30, width, 30), Qt.AlignmentFlag.AlignCenter, self.label)
