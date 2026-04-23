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
        self.line_color = QColor("#1890ff")
        self.point_color = QColor("#ffffff")
        
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
            
        # 先绘制折线主体。
        pen = QPen(self.line_color, 2)
        painter.setPen(pen)
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i+1])
            
        # 再绘制折线下方的渐变区域，增强层次感。
        path = [QPointF(padding, height - padding)] + points + [QPointF(width - padding, height - padding)]
        gradient = QLinearGradient(0, 0, 0, height)
        # 颜色由上到下逐渐透明，形成类似设计稿中的紫蓝过渡效果。
        gradient.setColorAt(0, QColor(114, 46, 209, 80))  # 顶部偏紫
        gradient.setColorAt(0.5, QColor(24, 144, 255, 40))  # 中段偏蓝
        gradient.setColorAt(1, QColor(24, 144, 255, 0))
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
        # 为柱子准备一组从青色到紫色的渐变基色，循环复用。
        self.bar_colors = [
            "#00F0FF", "#00F0FF",  # 青色
            "#00A2FF", "#00A2FF",  # 天蓝
            "#1890FF", "#1890FF",  # 蓝色
            "#4367FF", "#4367FF",  # 靛蓝
            "#722ED1", "#722ED1",  # 紫色
            "#9254DE", "#9254DE"   # 浅紫
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
            color = QColor(self.bar_colors[i % len(self.bar_colors)])
            
            # 每个柱子使用纵向渐变，顶部亮、底部稍暗，增强立体感。
            gradient = QLinearGradient(x, y, x, y + h)
            gradient.setColorAt(0, color)
            gradient.setColorAt(1, color.darker(120))
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, 3, 3)
            
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
    def __init__(self, label, value, unit="kg", color="#1890ff", parent=None):
        super().__init__(parent)
        self.label = label
        self.value = value
        self.unit = unit
        self.color = QColor(color)
        # 当前按固定最大值换算占比，后续如接真实容量可改为动态传入。
        self.max_value = 1000
        
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
        
        # 先绘制背景槽，表示总容量范围。
        bar_y = 30
        bar_height = height - 70  # 底部留给仓库名称标签。
        bar_width = width * 0.5
        bar_x = (width - bar_width) / 2
        
        bg_rect = QRectF(bar_x, bar_y, bar_width, bar_height)
        painter.setBrush(QBrush(QColor("#2A3038")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(bg_rect, 6, 6)
        
        # 再绘制填充部分，高度按当前值 / 最大值计算。
        fill_height = (self.value / self.max_value) * bar_height
        fill_rect = QRectF(bar_x, bar_y + bar_height - fill_height, bar_width, fill_height)
        
        gradient = QLinearGradient(0, bar_y + bar_height - fill_height, 0, bar_y + bar_height)
        if self.color.name() == "#1890ff":  # 蓝色系仓储条
            gradient.setColorAt(0, QColor("#1890FF"))
            gradient.setColorAt(1, QColor("#0050B3"))
        else:  # 橙黄色系仓储条
            gradient.setColorAt(0, QColor("#FFA940"))
            gradient.setColorAt(1, QColor("#D46B08"))
        
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(fill_rect, 6, 6)
        
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
