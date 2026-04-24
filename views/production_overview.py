from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QFrame, QGridLayout, QPushButton, QStackedWidget,
                             QGraphicsOpacityEffect, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, QDateTime, pyqtSignal, QEvent, QEasingCurve, QPropertyAnimation, QPoint, QPointF
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QPen, QColor, QPainterPath
import os
import time
from pathlib import Path

from views.components.charts import LineChart, BarChart, StorageBar


class StatusCard(QFrame):
    """右侧设备状态卡片组件。

    在总览页中，通过独立的 QFrame 展示某一类设备的总数量、运行数量及代表性图标。
    支持自定义图标背景色以增强视觉区分度。
    """
    def __init__(self, title, icon_path, total="99", running="99", icon_bg="#1890ff", parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #1A1F26;
                border: 1px solid #2A3038;
                border-radius: 12px;
            }}
        """)
        self.setFixedHeight(85)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        
        # 图标容器：通过独立圆形背景块增强图标辨识度。
        icon_container = QFrame()
        icon_container.setFixedSize(40, 40)
        icon_container.setStyleSheet(f"""
            QFrame {{
                background-color: {icon_bg};
                border-radius: 20px;
                border: none;
            }}
        """)
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(8, 8, 8, 8)
        
        icon_label = QLabel()
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_layout.addWidget(icon_label)
        
        layout.addWidget(icon_container)
        
        # 文本区域：上方标题，下方显示总数和运行数量。
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        title_label = QLabel(title)
        title_label.setStyleSheet("color: white; font-size: 15px; font-weight: bold; border: none;")
        info_layout.addWidget(title_label)
        
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)
        
        total_label = QLabel(f"总数 <font color='#FFFFFF'>{total}</font>")
        total_label.setStyleSheet("color: #8C8C8C; font-size: 12px; border: none;")
        stats_layout.addWidget(total_label)
        
        running_label = QLabel(f"运行 <font color='#FFFFFF'>{running}</font>")
        running_label.setStyleSheet("color: #8C8C8C; font-size: 12px; border: none;")
        stats_layout.addWidget(running_label)
        
        info_layout.addLayout(stats_layout)
        layout.addLayout(info_layout)
        layout.addStretch()


class CircleMark(QLabel):
    """圆形开始/结束标识。"""
    def __init__(self, text, color="#10B981", parent=None):
        super().__init__(text, parent)
        self.setFixedSize(76, 76)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color}33;
                border: 2px solid {color};
                color: {color};
                border-radius: 38px;
                font-size: 18px;
                font-weight: 700;
            }}
        """)


class ProcessCard(QFrame):
    """智能生产流程中的设备节点卡片 (高保真版)。"""
    def __init__(self, title, subtitle, status, icon_path=None, accent="#1890FF", parent=None):
        super().__init__(parent)
        self._status = status
        self.setFixedSize(280, 104)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #2C3036;
                border: 1px solid #3A4454;
                border-radius: 16px;
            }}
        """)
        
        # 整体布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 顶部装饰条
        accent_bar = QFrame()
        accent_bar.setFixedHeight(6)
        accent_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {accent};
                border-top-left-radius: 16px;
                border-top-right-radius: 16px;
                border: none;
            }}
        """)
        main_layout.addWidget(accent_bar)

        # 内容区
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(16, 12, 16, 12)
        content_layout.setSpacing(12)

        # 左侧图标
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(44, 44)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet(f"""
            QLabel {{
                background-color: {accent};
                border-radius: 22px;
                border: none;
            }}
        """)
        if icon_path and os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.icon_label.setPixmap(pixmap)
        content_layout.addWidget(self.icon_label)

        # 中间文本
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: 700; border: none;")
        text_layout.addWidget(title_label)

        if subtitle:
            sub_label = QLabel(subtitle)
            sub_label.setStyleSheet("color: #9098A4; font-size: 14px; border: none;")
            text_layout.addWidget(sub_label)
        content_layout.addLayout(text_layout, 1)

        # 右侧状态胶囊
        self.status_label = QLabel()
        self.set_status(status)
        content_layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignVCenter)

        main_layout.addWidget(content_widget)

        # 左右连接点 (仅视觉)
        self.dot_l = QFrame(self)
        self.dot_l.setFixedSize(12, 12)
        self.dot_l.setStyleSheet("background-color: #007AFF; border-radius: 6px; border: none;")
        self.dot_l.move(-6, 46)
        
        self.dot_r = QFrame(self)
        self.dot_r.setFixedSize(12, 12)
        self.dot_r.setStyleSheet("background-color: #007AFF; border-radius: 6px; border: none;")
        self.dot_r.move(274, 46)

    def set_status(self, status):
        self._status = status
        status_color = "#10B981"
        if status in {"关闭", "停止", "异常"}:
            status_color = "#FF4D4F"
        elif status in {"正常", "开启"}:
            status_color = "#10B981"

        self.status_label.setText(status)
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {status_color};
                background-color: {status_color}26;
                border: 1px solid {status_color}66;
                border-radius: 14px;
                padding: 4px 12px;
                font-size: 14px;
                font-weight: 600;
            }}
        """)


class SmartStageCard(QFrame):
    """底部工位信息卡片。"""
    clicked = pyqtSignal()

    def __init__(self, title, subtitle, running=False, active=False, parent=None):
        super().__init__(parent)
        self._selected = active
        self._running = running
        self.setFixedSize(240, 130)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_selected_style()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #FFFFFF; font-size: 18px; font-weight: 700; border: none;")
        top_layout.addWidget(title_label)
        top_layout.addStretch()

        self.status_label = QLabel()
        self.set_running(running)
        top_layout.addWidget(self.status_label)
        layout.addLayout(top_layout)

        sub_label = QLabel(subtitle)
        sub_label.setStyleSheet("color: rgba(255, 255, 255, 0.75); font-size: 14px; border: none;")
        sub_label.setWordWrap(True)
        layout.addWidget(sub_label)
        layout.addStretch()

    def _apply_selected_style(self):
        if self._selected:
            self.setStyleSheet("""
                QFrame {
                    background-color: #0A84FF;
                    border: 1px solid #0A84FF;
                    border-radius: 12px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #1A1F26;
                    border: 1px solid #2A3038;
                    border-radius: 12px;
                }
                QFrame:hover {
                    border: 1px solid #3A4658;
                }
            """)

    def set_selected(self, selected):
        self._selected = selected
        self._apply_selected_style()

    def set_running(self, running):
        self._running = running
        if running:
            status_bg = "rgba(0, 188, 101, 0.2)"
            status_border = "rgba(0, 188, 101, 0.42)"
            status_text = "#00D084"
            status = "运行中"
        else:
            status_bg = "rgba(140, 140, 140, 0.2)"
            status_border = "rgba(140, 140, 140, 0.45)"
            status_text = "#BFBFBF"
            status = "未启动"

        self.status_label.setText(status)
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {status_text};
                background-color: {status_bg};
                border: 1px solid {status_border};
                border-radius: 10px;
                padding: 1px 8px;
                font-size: 11px;
                font-weight: 600;
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class ProductionFlowCanvas1(QWidget):
    """1#平台智能上料流程画布。"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.base_img_path = str(Path(__file__).resolve().parents[1] / "resources" / "images")
        self.wf_img_path = os.path.join(self.base_img_path, "workflow")
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.addStretch()

        h_layout = QHBoxLayout()
        h_layout.addStretch()

        flow_layout = QVBoxLayout()
        flow_layout.setSpacing(60)

        # 第一行: 开始 -> 仓1 -> 204_1 -> 003 -> 仓2
        self.row1 = QHBoxLayout()
        self.row1.setSpacing(40)
        self.row1.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.start_node = CircleMark("开始", "#10B981")
        self.row1.addWidget(self.start_node)

        self.node1 = ProcessCard("智能料仓", "日杂料", "停止", os.path.join(self.wf_img_path, "bin_icon.svg"), "#F759AB")
        self.node2 = ProcessCard("204双通道光选机", "", "停止", os.path.join(self.wf_img_path, "sorter_logo.svg"), "#0A84FF")
        self.node3 = ProcessCard("003皮带输送机", "", "停止", os.path.join(self.base_img_path, "icon_transport.svg"), "#13C2FF")
        self.node4 = ProcessCard("智能料仓", "三色瓶", "停止", os.path.join(self.wf_img_path, "bin_icon.svg"), "#F759AB")
        
        for n in [self.node1, self.node2, self.node3, self.node4]:
            self.row1.addWidget(n)
        flow_layout.addLayout(self.row1)

        # 第二行: 结束 <- 001 <- 204_2 <- 吹瓶机
        self.row2 = QHBoxLayout()
        self.row2.setSpacing(40)
        self.row2.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.end_node = CircleMark("结束", "#FF4D4F")
        self.node8 = ProcessCard("001皮带输送机", "", "停止", os.path.join(self.base_img_path, "icon_transport.svg"), "#13C2FF")
        self.node7 = ProcessCard("204双通道光选机", "", "停止", os.path.join(self.wf_img_path, "sorter_logo.svg"), "#0A84FF")
        self.node6 = ProcessCard("吹瓶机", "", "停止", os.path.join(self.wf_img_path, "blower_icon.svg"), "#722ED1")

        # 为了对齐，第二行前面加一点 stretch 或固定间距
        self.row2.addWidget(self.end_node)
        self.row2.addSpacing(120) # 结束节点和 001 之间的间距
        self.row2.addWidget(self.node8)
        self.row2.addWidget(self.node7)
        self.row2.addWidget(self.node6)
        
        flow_layout.addLayout(self.row2)

        h_layout.addLayout(flow_layout)
        h_layout.addStretch()

        main_layout.addLayout(h_layout)
        main_layout.addStretch()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        pen = QPen(QColor("#007AFF"), 3)
        painter.setPen(pen)

        # 绘制第一行连线
        self._draw_connection(painter, self.start_node, self.node1)
        self._draw_connection(painter, self.node1, self.node2)
        self._draw_connection(painter, self.node2, self.node3)
        self._draw_connection(painter, self.node3, self.node4)

        # 绘制 S 形转折连线 (从 node4 右侧到 node6 右侧)
        p4 = QPointF(self.node4.mapTo(self, self.node4.dot_r.geometry().center()))
        p6 = QPointF(self.node6.mapTo(self, self.node6.dot_r.geometry().center()))
        
        # 绘制简单的半圆弧或三次贝塞尔曲线
        mid_x = max(p4.x(), p6.x()) + 80
        curve_path = QPainterPath()
        curve_path.moveTo(p4)
        curve_path.cubicTo(mid_x, p4.y(), mid_x, p6.y(), p6.x(), p6.y())
        painter.drawPath(curve_path)

        # 绘制第二行连线 (逆向: 吹瓶机 -> 204_2 -> 001 -> 结束)
        self._draw_connection(painter, self.node7, self.node6)
        self._draw_connection(painter, self.node8, self.node7)
        
        # 结束节点的连线从 001 的左侧到结束节点的右侧
        p8_l = QPointF(self.node8.mapTo(self, self.node8.dot_l.geometry().center()))
        p_end_r = QPointF(self.end_node.geometry().center() + QPoint(38, 0))
        painter.drawLine(p8_l, p_end_r)

    def _draw_connection(self, painter, node_a, node_b):
        # 获取节点 a 的右连接点 and 节点 b 的左连接点
        if hasattr(node_a, "dot_r"):
            p1 = QPointF(node_a.mapTo(self, node_a.dot_r.geometry().center()))
        else:
            # 对于 CircleMark
            p1 = QPointF(node_a.geometry().center() + QPoint(38, 0))
            
        if hasattr(node_b, "dot_l"):
            p2 = QPointF(node_b.mapTo(self, node_b.dot_l.geometry().center()))
        else:
            p2 = QPointF(node_b.geometry().center() - QPoint(38, 0))
            
        painter.drawLine(p1, p2)


class ProductionFlowCanvas2(QWidget):
    """三色瓶分选流程画布。"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.base_img_path = str(Path(__file__).resolve().parents[1] / "resources" / "images")
        self.wf_img_path = os.path.join(self.base_img_path, "workflow")
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 20, 40, 20)
        main_layout.addStretch()

        h_layout = QHBoxLayout()
        h_layout.addStretch()

        flow_layout = QVBoxLayout()
        flow_layout.setSpacing(40)

        # 第一行: 从左到右
        row1 = QHBoxLayout()
        row1.setSpacing(30)
        row1.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.start_node = CircleMark("开始", "#10B981")
        row1.addWidget(self.start_node)

        self.node1 = ProcessCard("缓存料仓", "3A瓶", "停止", os.path.join(self.wf_img_path, "bin_icon.svg"), "#F759AB")
        self.node2 = ProcessCard("吹瓶机", "", "停止", os.path.join(self.wf_img_path, "blower_icon.svg"), "#722ED1")
        self.node3 = ProcessCard("缓存料仓", "绿瓶", "停止", os.path.join(self.wf_img_path, "bin_icon.svg"), "#F759AB")
        self.node4 = ProcessCard("吹瓶机", "", "停止", os.path.join(self.wf_img_path, "blower_icon.svg"), "#722ED1")
        
        for n in [self.node1, self.node2, self.node3, self.node4]:
            row1.addWidget(n)
        flow_layout.addLayout(row1)

        # 第二行: 从右到左
        row2 = QHBoxLayout()
        row2.setSpacing(30)
        row2.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.node8 = ProcessCard("智能料仓", "二级蓝白", "停止", os.path.join(self.wf_img_path, "bin_icon.svg"), "#F759AB")
        self.node7 = ProcessCard("吹瓶机", "", "停止", os.path.join(self.wf_img_path, "blower_icon.svg"), "#722ED1")
        self.node6 = ProcessCard("AI智能光选机", "(弓184) 3A瓶光选机", "停止", os.path.join(self.wf_img_path, "ai_sorter_icon.svg"), "#0A84FF")
        self.node5 = ProcessCard("皮带输送机", "3A尾料皮带", "停止", os.path.join(self.base_img_path, "icon_transport.svg"), "#0A84FF")
        
        row2.addSpacing(106) # 对齐偏移
        for n in [self.node5, self.node6, self.node7, self.node8]:
            row2.addWidget(n)
        flow_layout.addLayout(row2)

        # 第三行: 从左到右
        row3 = QHBoxLayout()
        row3.setSpacing(30)
        row3.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.node9 = ProcessCard("204双通道光选机", "", "停止", os.path.join(self.wf_img_path, "ai_sorter_icon.svg"), "#0A84FF")
        self.node10 = ProcessCard("吹瓶机", "", "停止", os.path.join(self.wf_img_path, "blower_icon.svg"), "#722ED1")
        self.end_node = CircleMark("结束", "#FF4D4F")
        
        row3.addSpacing(106)
        row3.addWidget(self.node9)
        row3.addWidget(self.node10)
        row3.addWidget(self.end_node)
        flow_layout.addLayout(row3)

        h_layout.addLayout(flow_layout)
        h_layout.addStretch()

        main_layout.addLayout(h_layout)
        main_layout.addStretch()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor("#007AFF"), 3)
        painter.setPen(pen)

        # 第一行连线
        self._draw_connection(painter, self.start_node, self.node1)
        self._draw_connection(painter, self.node1, self.node2)
        self._draw_connection(painter, self.node2, self.node3)
        self._draw_connection(painter, self.node3, self.node4)

        # 第一行到第二行 (N4右 -> N8右)
        p4 = QPointF(self.node4.mapTo(self, self.node4.dot_r.geometry().center()))
        p8 = QPointF(self.node8.mapTo(self, self.node8.dot_r.geometry().center()))
        mid_x1 = max(p4.x(), p8.x()) + 60
        curve_path1 = QPainterPath()
        curve_path1.moveTo(p4)
        curve_path1.cubicTo(mid_x1, p4.y(), mid_x1, p8.y(), p8.x(), p8.y())
        painter.drawPath(curve_path1)

        # 第二行连线 (逆向)
        self._draw_connection_reverse(painter, self.node8, self.node7)
        self._draw_connection_reverse(painter, self.node7, self.node6)
        self._draw_connection_reverse(painter, self.node6, self.node5)

        # 第二行到第三行 (N5左 -> N9左)
        p5 = QPointF(self.node5.mapTo(self, self.node5.dot_l.geometry().center()))
        p9 = QPointF(self.node9.mapTo(self, self.node9.dot_l.geometry().center()))
        mid_x2 = min(p5.x(), p9.x()) - 60
        curve_path2 = QPainterPath()
        curve_path2.moveTo(p5)
        curve_path2.cubicTo(mid_x2, p5.y(), mid_x2, p9.y(), p9.x(), p9.y())
        painter.drawPath(curve_path2)

        # 第三行连线
        self._draw_connection(painter, self.node9, self.node10)
        
        # 最后一个节点到结束节点
        p10 = QPointF(self.node10.mapTo(self, self.node10.dot_r.geometry().center()))
        p_end = QPointF(self.end_node.geometry().center() - QPoint(38, 0))
        painter.drawLine(p10, p_end)

    def _draw_connection(self, painter, node_a, node_b):
        if hasattr(node_a, "dot_r"):
            p1 = QPointF(node_a.mapTo(self, node_a.dot_r.geometry().center()))
        else:
            p1 = QPointF(node_a.geometry().center() + QPoint(38, 0))
        if hasattr(node_b, "dot_l"):
            p2 = QPointF(node_b.mapTo(self, node_b.dot_l.geometry().center()))
        else:
            p2 = QPointF(node_b.geometry().center() - QPoint(38, 0))
        painter.drawLine(p1, p2)

    def _draw_connection_reverse(self, painter, node_a, node_b):
        p1 = QPointF(node_a.mapTo(self, node_a.dot_l.geometry().center()))
        p2 = QPointF(node_b.mapTo(self, node_b.dot_r.geometry().center()))
        painter.drawLine(p1, p2)


class ProductionFlowCanvas3(QWidget):
    """3A瓶脱标工艺流程画布。"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.base_img_path = str(Path(__file__).resolve().parents[1] / "resources" / "images")
        self.wf_img_path = os.path.join(self.base_img_path, "workflow")
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.addStretch()

        h_layout = QHBoxLayout()
        h_layout.addStretch()

        flow_layout = QVBoxLayout()
        flow_layout.setSpacing(60)

        # 第一行: 从左到右
        row1 = QHBoxLayout()
        row1.setSpacing(30)
        row1.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.start_node = CircleMark("开始", "#10B981")
        row1.addWidget(self.start_node)

        self.node1 = ProcessCard("缓存料仓", "3A成品仓", "停止", os.path.join(self.wf_img_path, "bin_icon.svg"), "#F759AB")
        self.node2 = ProcessCard("吹瓶机", "三通道风机切换", "停止", os.path.join(self.wf_img_path, "blower_icon.svg"), "#0A84FF")
        self.node3 = ProcessCard("风机", "标签纸风机", "停止", os.path.join(self.wf_img_path, "fan_icon.svg"), "#0A84FF")
        self.node4 = ProcessCard("脱标机", "圆瓶脱标机", "停止", os.path.join(self.wf_img_path, "labeler_icon.svg"), "#722ED1")
        
        for n in [self.node1, self.node2, self.node3, self.node4]:
            row1.addWidget(n)
        flow_layout.addLayout(row1)

        # 第二行: 从右到左
        row2 = QHBoxLayout()
        row2.setSpacing(30)
        row2.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.end_node = CircleMark("结束", "#FF4D4F")
        self.node7 = ProcessCard("智能料仓", "3A瓶", "停止", os.path.join(self.wf_img_path, "bin_icon.svg"), "#F759AB")
        self.node6 = ProcessCard("料仓输送机", "3A瓶卸料仓门", "停止", os.path.join(self.base_img_path, "icon_transport.svg"), "#0A84FF")
        self.node5 = ProcessCard("皮带输送机", "3A瓶卸料输送皮带", "停止", os.path.join(self.base_img_path, "icon_transport.svg"), "#0A84FF")
        
        row2.addSpacing(270) # 使得 N7, N6, N5 与上一行的 N2, N3, N4 对齐
        row2.addWidget(self.end_node)
        for n in [self.node7, self.node6, self.node5]:
            row2.addWidget(n)
        flow_layout.addLayout(row2)

        h_layout.addLayout(flow_layout)
        h_layout.addStretch()

        main_layout.addLayout(h_layout)
        main_layout.addStretch()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor("#007AFF"), 3)
        painter.setPen(pen)

        # 第一行连线
        self._draw_connection(painter, self.start_node, self.node1)
        self._draw_connection(painter, self.node1, self.node2)
        self._draw_connection(painter, self.node2, self.node3)
        self._draw_connection(painter, self.node3, self.node4)

        # 第一行到第二行 (N4右 -> N5右)
        p4 = QPointF(self.node4.mapTo(self, self.node4.dot_r.geometry().center()))
        p5 = QPointF(self.node5.mapTo(self, self.node5.dot_r.geometry().center()))
        mid_x = max(p4.x(), p5.x()) + 60
        curve_path = QPainterPath()
        curve_path.moveTo(p4)
        curve_path.cubicTo(mid_x, p4.y(), mid_x, p5.y(), p5.x(), p5.y())
        painter.drawPath(curve_path)

        # 第二行连线 (逆向)
        self._draw_connection_reverse(painter, self.node5, self.node6)
        self._draw_connection_reverse(painter, self.node6, self.node7)
        
        # 最后一个节点到结束节点
        p7 = QPointF(self.node7.mapTo(self, self.node7.dot_l.geometry().center()))
        p_end = QPointF(self.end_node.geometry().center() + QPoint(38, 0)) # 结束节点在左侧，所以接它的右边缘，等下改这里。由于 end_node 在最左，所以是从 node7 左连到 end_node 右。
        painter.drawLine(p7, p_end)

    def _draw_connection(self, painter, node_a, node_b):
        if hasattr(node_a, "dot_r"):
            p1 = QPointF(node_a.mapTo(self, node_a.dot_r.geometry().center()))
        else:
            p1 = QPointF(node_a.geometry().center() + QPoint(38, 0))
        if hasattr(node_b, "dot_l"):
            p2 = QPointF(node_b.mapTo(self, node_b.dot_l.geometry().center()))
        else:
            p2 = QPointF(node_b.geometry().center() - QPoint(38, 0))
        painter.drawLine(p1, p2)

    def _draw_connection_reverse(self, painter, node_a, node_b):
        p1 = QPointF(node_a.mapTo(self, node_a.dot_l.geometry().center()))
        p2 = QPointF(node_b.mapTo(self, node_b.dot_r.geometry().center()))
        painter.drawLine(p1, p2)


class ProductionFlowCanvas4(QWidget):
    """绿瓶脱标工艺流程画布。"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.base_img_path = str(Path(__file__).resolve().parents[1] / "resources" / "images")
        self.wf_img_path = os.path.join(self.base_img_path, "workflow")
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 20, 40, 20)
        main_layout.addStretch()

        h_layout = QHBoxLayout()
        h_layout.addStretch()

        flow_layout = QVBoxLayout()
        flow_layout.setSpacing(40)

        # 第一行: 从左到右
        row1 = QHBoxLayout()
        row1.setSpacing(30)
        row1.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.start_node = CircleMark("开始", "#10B981")
        row1.addWidget(self.start_node)

        self.node1 = ProcessCard("料仓输送机", "3A瓶卸料仓门", "停止", os.path.join(self.base_img_path, "icon_transport.svg"), "#0A84FF")
        self.node2 = ProcessCard("皮带输送机", "3A瓶卸料输送皮带", "停止", os.path.join(self.base_img_path, "icon_transport.svg"), "#0A84FF")
        self.node3 = ProcessCard("缓存料仓", "绿瓶缓存仓", "停止", os.path.join(self.wf_img_path, "bin_icon.svg"), "#F759AB")
        self.node4 = ProcessCard("吹瓶机", "三通道风机切换", "停止", os.path.join(self.wf_img_path, "blower_icon.svg"), "#0A84FF")
        
        for n in [self.node1, self.node2, self.node3, self.node4]:
            row1.addWidget(n)
        flow_layout.addLayout(row1)

        # 第二行: 从右到左 (界面显示顺序为 N8, N7, N6, N5)
        row2 = QHBoxLayout()
        row2.setSpacing(30)
        row2.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.node8 = ProcessCard("料仓输送机", "绿瓶卸料仓门", "停止", os.path.join(self.base_img_path, "icon_transport.svg"), "#0A84FF")
        self.node7 = ProcessCard("皮带输送机", "3A瓶卸料输送皮带", "停止", os.path.join(self.base_img_path, "icon_transport.svg"), "#0A84FF")
        self.node6 = ProcessCard("脱标机", "圆瓶脱标机", "停止", os.path.join(self.wf_img_path, "labeler_icon.svg"), "#722ED1")
        self.node5 = ProcessCard("风机", "标签纸风机", "停止", os.path.join(self.wf_img_path, "fan_icon.svg"), "#0A84FF")

        row2.addSpacing(106) # 对齐偏移
        for n in [self.node8, self.node7, self.node6, self.node5]:
            row2.addWidget(n)
        flow_layout.addLayout(row2)

        # 第三行: 从左到右
        row3 = QHBoxLayout()
        row3.setSpacing(30)
        row3.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.node9 = ProcessCard("智能料仓", "3A瓶", "停止", os.path.join(self.wf_img_path, "bin_icon.svg"), "#F759AB")
        self.end_node = CircleMark("结束", "#FF4D4F")
        
        row3.addSpacing(106)
        row3.addWidget(self.node9)
        row3.addWidget(self.end_node)
        flow_layout.addLayout(row3)

        h_layout.addLayout(flow_layout)
        h_layout.addStretch()

        main_layout.addLayout(h_layout)
        main_layout.addStretch()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor("#007AFF"), 3)
        painter.setPen(pen)

        # 第一行连线
        self._draw_connection(painter, self.start_node, self.node1)
        self._draw_connection(painter, self.node1, self.node2)
        self._draw_connection(painter, self.node2, self.node3)
        self._draw_connection(painter, self.node3, self.node4)

        # 第一行到第二行 (N4右 -> N5右)
        p4 = QPointF(self.node4.mapTo(self, self.node4.dot_r.geometry().center()))
        p5 = QPointF(self.node5.mapTo(self, self.node5.dot_r.geometry().center()))
        mid_x = max(p4.x(), p5.x()) + 60
        curve_path1 = QPainterPath()
        curve_path1.moveTo(p4)
        curve_path1.cubicTo(mid_x, p4.y(), mid_x, p5.y(), p5.x(), p5.y())
        painter.drawPath(curve_path1)

        # 第二行连线 (逆向)
        self._draw_connection_reverse(painter, self.node5, self.node6)
        self._draw_connection_reverse(painter, self.node6, self.node7)
        self._draw_connection_reverse(painter, self.node7, self.node8)

        # 第二行到第三行 (N8左 -> N9左)
        p8 = QPointF(self.node8.mapTo(self, self.node8.dot_l.geometry().center()))
        p9 = QPointF(self.node9.mapTo(self, self.node9.dot_l.geometry().center()))
        mid_x2 = min(p8.x(), p9.x()) - 60
        curve_path2 = QPainterPath()
        curve_path2.moveTo(p8)
        curve_path2.cubicTo(mid_x2, p8.y(), mid_x2, p9.y(), p9.x(), p9.y())
        painter.drawPath(curve_path2)

        # 第三行连线
        self._draw_connection(painter, self.node9, self.end_node)

    def _draw_connection(self, painter, node_a, node_b):
        if hasattr(node_a, "dot_r"):
            p1 = QPointF(node_a.mapTo(self, node_a.dot_r.geometry().center()))
        else:
            p1 = QPointF(node_a.geometry().center() + QPoint(38, 0))
        if hasattr(node_b, "dot_l"):
            p2 = QPointF(node_b.mapTo(self, node_b.dot_l.geometry().center()))
        else:
            p2 = QPointF(node_b.geometry().center() - QPoint(38, 0))
        painter.drawLine(p1, p2)

    def _draw_connection_reverse(self, painter, node_a, node_b):
        p1 = QPointF(node_a.mapTo(self, node_a.dot_l.geometry().center()))
        p2 = QPointF(node_b.mapTo(self, node_b.dot_r.geometry().center()))
        painter.drawLine(p1, p2)


class ProductionOverview(QWidget):
    """生产总览页。

    页面主要由顶部标题区和下方网格内容区组成，内容区再拆分为：
    - 产线能耗折线图；
    - 智能仓储料位条；
    - 智能设备状态卡片；
    - 生产统计柱状图。
    """
    secret_triggered = pyqtSignal()
    
    def __init__(self, vm, parent=None):
        super().__init__(parent)
        self.vm = vm
        self.base_path = str(Path(__file__).resolve().parents[1] / "resources" / "images")
        # 记录 logo 点击时间，用于实现“短时间多次点击”的隐藏入口。
        self.click_times = []
        self._tab_fade_anim = None
        self.btn_overview = None
        self.btn_smart_prod = None
        self.content_stack = None
        self.logo_label = None
        self.start_btn = None
        self.smart_stop_btn = None
        self.stage_cards = []
        self._flow_names = [
            "1#平台智能上料",
            "三色瓶分选",
            "3A瓶脱标工艺",
            "绿瓶脱标工艺",
        ]
        self._start_btn_base_text = "启动流程"
        self._loading_dot_step = 0
        self._is_process_running = False
        self._running_stage_index = None
        self._pending_flow_action = None
        self._pending_flow_name = None
        self._loading_timer = QTimer(self)
        self._loading_timer.timeout.connect(self._update_start_btn_loading_text)
        self._init_ui()
        self._bind_viewmodel()

    def _bind_viewmodel(self):
        self.vm.flow_control_started.connect(self._on_flow_control_started)
        self.vm.flow_control_succeeded.connect(self._on_flow_control_succeeded)
        self.vm.flow_control_failed.connect(self._on_flow_control_failed)
        
    def _init_ui(self):
        """构建总览页所有静态 UI。"""
        self.setObjectName("ProductionOverview")
        self.setStyleSheet("background-color: #0B0E14;")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 15, 25, 25)
        main_layout.setSpacing(20)
        
        # --- HEADER ---
        header_layout = QHBoxLayout()
        
        # Logo：除展示品牌外，也承担隐藏入口触发区域。
        logo_label = QLabel()
        logo_path = os.path.join(self.base_path, "logo.svg")
        if os.path.exists(logo_path):
            logo_label.setPixmap(QPixmap(logo_path).scaled(140, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo_label.setCursor(Qt.CursorShape.PointingHandCursor)
        logo_label.installEventFilter(self)
        self.logo_label = logo_label
        header_layout.addWidget(logo_label)
        
        header_layout.addStretch()
        
        # 顶部页签当前仅做视觉展示，实际页面切换通常由上层容器接管。
        tabs_container = QFrame()
        tabs_container.setStyleSheet("""
            QFrame {
                background-color: #1A1F26;
                border-radius: 22px;
                padding: 4px;
            }
        """)
        tabs_layout = QHBoxLayout(tabs_container)
        tabs_layout.setContentsMargins(4, 4, 4, 4)
        tabs_layout.setSpacing(0)
        
        self.btn_overview = QPushButton("总览")
        self.btn_overview.setFixedSize(110, 36)
        self.btn_smart_prod = QPushButton("智能生产")
        self.btn_smart_prod.setFixedSize(110, 36)
        self._update_tab_styles(active_smart=False)
        self.btn_overview.clicked.connect(lambda: self._switch_tab(0))
        self.btn_smart_prod.clicked.connect(lambda: self._switch_tab(1))

        tabs_layout.addWidget(self.btn_overview)
        tabs_layout.addWidget(self.btn_smart_prod)
        header_layout.addWidget(tabs_container)
        
        header_layout.addStretch()
        
        # 右上角通知按钮和实时时间。
        notif_btn = QPushButton()
        notif_btn.setFixedSize(44, 44)
        notif_path = os.path.join(self.base_path, "notification.svg")
        if os.path.exists(notif_path):
            notif_btn.setIcon(QIcon(notif_path))
        notif_btn.setStyleSheet("background-color: #1A1F26; border-radius: 22px; border: none;")
        header_layout.addWidget(notif_btn)
        
        self.time_label = QLabel()
        self.time_label.setStyleSheet("color: white; font-size: 16px; margin-left: 15px; font-family: 'Inter';")
        header_layout.addWidget(self.time_label)
        
        # 使用轻量 QTimer 每秒刷新一次界面时间。
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_time)
        self.timer.start(1000)
        self._update_time()
        
        main_layout.addLayout(header_layout)
        
        # --- CONTENT ---
        self.content_stack = QStackedWidget()
        self.content_stack.setContentsMargins(0, 0, 0, 0)
        self.content_stack.addWidget(self._build_overview_page())
        self.content_stack.addWidget(self._build_smart_production_page())
        main_layout.addWidget(self.content_stack)

    def _build_overview_page(self):
        page = QWidget()
        content_layout = QGridLayout(page)
        content_layout.setSpacing(20)
        
        # 左上：产线能耗趋势图。
        energy_card = self._create_card("产线能耗统计")
        energy_chart = LineChart()
        energy_card.layout().addWidget(energy_chart)
        content_layout.addWidget(energy_card, 0, 0)
        
        # 中上：多个缓存仓料位条并排展示。
        storage_card = self._create_card("智能仓储")
        storage_layout = QHBoxLayout()
        storage_layout.setSpacing(10)
        storage_values = {
            "三色缓存仓": 206,
            "3A缓存仓": 601,
            "二级缓存仓": 498,
            "杂瓶缓存仓": 297,
        }
        storage_max_value = max(storage_values.values())
        storage_layout.addWidget(StorageBar("三色缓存仓", storage_values["三色缓存仓"], gradient_colors=("#36CFC9", "#08979C"), max_value=storage_max_value))
        storage_layout.addWidget(StorageBar("3A缓存仓", storage_values["3A缓存仓"], gradient_colors=("#FFC53D", "#FA8C16"), max_value=storage_max_value))
        storage_layout.addWidget(StorageBar("二级缓存仓", storage_values["二级缓存仓"], gradient_colors=("#B37FEB", "#722ED1"), max_value=storage_max_value))
        storage_layout.addWidget(StorageBar("杂瓶缓存仓", storage_values["杂瓶缓存仓"], gradient_colors=("#69C0FF", "#0958D9"), max_value=storage_max_value))
        storage_card.layout().addLayout(storage_layout)
        content_layout.addWidget(storage_card, 0, 1)
        
        # 右侧整列：设备状态卡片 + 紧急停止按钮。
        equip_container = QFrame()
        equip_container.setStyleSheet("background-color: #1A1F26; border-radius: 16px; border: 1px solid #2A3038;")
        equip_layout = QVBoxLayout(equip_container)
        equip_layout.setContentsMargins(15, 20, 15, 15)
        equip_layout.setSpacing(12)
        
        equip_title = QLabel("智能设备")
        equip_title.setStyleSheet("color: white; font-size: 18px; font-weight: bold; border: none; margin-bottom: 5px;")
        equip_layout.addWidget(equip_title)
        
        equip_layout.addWidget(StatusCard("输送设备", os.path.join(self.base_path, "icon_transport.svg"), total="12", running="10", icon_bg="#006D75"))
        equip_layout.addWidget(StatusCard("分拣设备", os.path.join(self.base_path, "icon_sorting.svg"), total="08", running="08", icon_bg="#096DD9"))
        equip_layout.addWidget(StatusCard("码垛设备", os.path.join(self.base_path, "rect_73.svg"), total="04", running="03", icon_bg="#722ED1"))
        equip_layout.addWidget(StatusCard("包装设备", os.path.join(self.base_path, "rect_74.svg"), total="06", running="06", icon_bg="#C41D7F"))
        
        equip_layout.addStretch()
        
        # 紧急停止按钮放在设备列底部，避免与主网格发生重叠。
        self.stop_btn = QPushButton("紧急停止\nSTOP")
        self.stop_btn.setFixedSize(180, 180)  # 通过大尺寸增强危险操作的视觉权重。
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF4D4F;
                color: white;
                border-radius: 90px;
                font-size: 22px;
                font-weight: bold;
                border: 12px solid #2A1A1A;
            }
            QPushButton:pressed {
                background-color: #D4380D;
            }
        """)
        self.stop_btn.clicked.connect(self._handle_emergency_stop_click)
        equip_layout.addWidget(self.stop_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        equip_layout.addSpacing(10)
        
        content_layout.addWidget(equip_container, 0, 2, 2, 1)
        
        # 左下和中下：生产统计柱状图，跨两列布局。
        prod_card = self._create_card("生产统计")
        prod_chart = BarChart()
        prod_card.layout().addWidget(prod_chart)
        content_layout.addWidget(prod_card, 1, 0, 1, 2)
        
        # 通过拉伸因子控制三列宽度，尽量贴近设计稿比例。
        content_layout.setColumnStretch(0, 4)  # 折线图列
        content_layout.setColumnStretch(1, 4)  # 仓储列
        content_layout.setColumnStretch(2, 2)  # 设备列相对更窄
        content_layout.setRowStretch(0, 4)
        content_layout.setRowStretch(1, 4)
        
        return page

    def _build_smart_production_page(self):
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(18)

        # 顶部操作区
        top_action = QHBoxLayout()
        top_action.addStretch()
        self.start_btn = QPushButton("启动流程")
        self.start_btn.setFixedSize(116, 52)
        self.start_btn.setStyleSheet("""
            QPushButton[state="default"] {
                background-color: #0A84FF;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 24px;
                font-weight: 700;
            }
            QPushButton[state="default"]:hover { background-color: #3199FF; }
            QPushButton[state="default"]:pressed { background-color: #066FD7; }
            QPushButton[state="loading"] {
                background-color: #2C7EDB;
                color: #EAF4FF;
                border: none;
                border-radius: 10px;
                font-size: 20px;
                font-weight: 700;
            }
            QPushButton[state="error"] {
                background-color: #632A2A;
                color: #FFB3B3;
                border: 1px solid #FF4D4F;
                border-radius: 10px;
                font-size: 20px;
                font-weight: 700;
            }
            QPushButton:disabled {
                background-color: #3C4A5E;
                color: #98A2B3;
            }
        """)
        self.start_btn.clicked.connect(self._handle_start_btn_click)
        self._set_start_btn_state("default")
        top_action.addWidget(self.start_btn)
        page_layout.addLayout(top_action)

        # 流程区（使用高保真画布）
        self.flow_stack = QStackedWidget()
        self.flow_stack.setStyleSheet("""
            QStackedWidget {
                background-color: #0B0E14;
                border: 1px solid #202733;
                border-radius: 14px;
            }
        """)
        
        # 1#平台智能上料 的流程
        self.flow_canvas_1 = ProductionFlowCanvas1()
        self.flow_stack.addWidget(self.flow_canvas_1)
        
        # 三色瓶分选
        self.flow_canvas_2 = ProductionFlowCanvas2()
        self.flow_stack.addWidget(self.flow_canvas_2)

        # 3A瓶脱标工艺
        self.flow_canvas_3 = ProductionFlowCanvas3()
        self.flow_stack.addWidget(self.flow_canvas_3)

        # 绿瓶脱标工艺
        self.flow_canvas_4 = ProductionFlowCanvas4()
        self.flow_stack.addWidget(self.flow_canvas_4)
        
        page_layout.addWidget(self.flow_stack)

        bottom_panel = QHBoxLayout()
        bottom_panel.setSpacing(12)

        left_arrow = QPushButton("‹")
        left_arrow.setFixedSize(56, 56)
        left_arrow.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.08);
                color: white;
                border: 1px solid #3A4454;
                border-radius: 28px;
                font-size: 42px;
            }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.16); }
            QPushButton:pressed { background-color: rgba(255, 255, 255, 0.22); }
            QPushButton:disabled {
                background-color: rgba(255, 255, 255, 0.05);
                color: #6B7280;
            }
        """)
        bottom_panel.addWidget(left_arrow, alignment=Qt.AlignmentFlag.AlignVCenter)

        bottom_cards = QHBoxLayout()
        bottom_cards.setSpacing(10)
        self.stage_cards = [
            SmartStageCard("1#平台智能上料", "前端处理原料流程: 圆瓶", running=False, active=True),
            SmartStageCard("三色瓶分选", "三色瓶分选工艺", running=False, active=False),
            SmartStageCard("3A瓶脱标工艺", "对3A瓶进行脱标，生产3A成品", running=False, active=False),
            SmartStageCard("绿瓶脱标工艺", "绿瓶脱标，生产绿瓶成品", running=False, active=False),
        ]
        for idx, card in enumerate(self.stage_cards):
            card.clicked.connect(lambda _=None, index=idx: self._set_active_stage_card(index))
            bottom_cards.addWidget(card)
        bottom_panel.addLayout(bottom_cards, 1)

        # 默认显示 1#平台智能上料 流程
        self.flow_stack.setCurrentIndex(0)

        right_arrow = QPushButton("›")
        right_arrow.setFixedSize(56, 56)
        right_arrow.setStyleSheet(left_arrow.styleSheet())
        bottom_panel.addWidget(right_arrow, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.smart_stop_btn = QPushButton("紧急停止\nSTOP")
        self.smart_stop_btn.setFixedSize(180, 180)
        self.smart_stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF4D4F;
                color: white;
                border-radius: 90px;
                font-size: 22px;
                font-weight: bold;
                border: 12px solid #2A1A1A;
            }
            QPushButton:hover { background-color: #FF7875; }
            QPushButton:pressed { background-color: #D4380D; }
            QPushButton:disabled {
                background-color: #914040;
                border-color: #3A2222;
                color: #D1BFBF;
            }
        """)
        self.smart_stop_btn.clicked.connect(self._handle_emergency_stop_click)
        bottom_panel.addWidget(self.smart_stop_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        page_layout.addLayout(bottom_panel)
        return page

    def _update_tab_styles(self, active_smart):
        active_style = """
            QPushButton {
                background-color: #0A84FF;
                color: white;
                border-radius: 18px;
                font-weight: bold;
                font-size: 15px;
                border: none;
            }
            QPushButton:hover { background-color: #2996FF; }
            QPushButton:pressed { background-color: #066FD7; }
            QPushButton:disabled {
                background-color: #2F3B4D;
                color: #7C8798;
            }
        """
        inactive_style = """
            QPushButton {
                background-color: transparent;
                color: #8C8C8C;
                border-radius: 18px;
                font-size: 15px;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.08);
                color: #D9D9D9;
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.14);
            }
            QPushButton:disabled {
                color: #5C6675;
            }
        """
        if active_smart:
            self.btn_overview.setStyleSheet(inactive_style)
            self.btn_smart_prod.setStyleSheet(active_style)
        else:
            self.btn_overview.setStyleSheet(active_style)
            self.btn_smart_prod.setStyleSheet(inactive_style)

    def _switch_tab(self, index):
        self._update_tab_styles(active_smart=(index == 1))
        self.content_stack.setCurrentIndex(index)
        current_page = self.content_stack.currentWidget()
        effect = QGraphicsOpacityEffect(current_page)
        current_page.setGraphicsEffect(effect)

        if self._tab_fade_anim:
            self._tab_fade_anim.stop()
        self._tab_fade_anim = QPropertyAnimation(effect, b"opacity", self)
        self._tab_fade_anim.setDuration(220)
        self._tab_fade_anim.setStartValue(0.0)
        self._tab_fade_anim.setEndValue(1.0)
        self._tab_fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._tab_fade_anim.finished.connect(lambda: current_page.setGraphicsEffect(None))
        self._tab_fade_anim.start()

    def _flow_name_from_index(self, index):
        if 0 <= index < len(self._flow_names):
            return self._flow_names[index]
        return ""

    def _flow_index_from_name(self, flow_name):
        try:
            return self._flow_names.index(flow_name)
        except ValueError:
            return -1

    def _get_current_flow_name(self):
        if not self.flow_stack:
            return ""
        return self._flow_name_from_index(self.flow_stack.currentIndex())

    def _get_running_flow_name(self):
        if self._running_stage_index is None:
            return ""
        return self._flow_name_from_index(self._running_stage_index)

    def _set_flow_action_pending(self, flow_name, action):
        self._pending_flow_name = flow_name or None
        self._pending_flow_action = action or None
        is_pending = bool(self._pending_flow_action)
        self._set_start_btn_state("loading" if is_pending else "default")
        if self.stop_btn:
            self.stop_btn.setEnabled(not is_pending)
        if self.smart_stop_btn:
            self.smart_stop_btn.setEnabled(not is_pending)

    def _show_flow_control_warning(self, message):
        QMessageBox.warning(self, "提示", message)

    def _on_flow_control_started(self, flow_name, action):
        self._set_flow_action_pending(flow_name, action)

    def _on_flow_control_succeeded(self, result):
        flow_name = result.get("flow_name", "") if isinstance(result, dict) else ""
        action = result.get("action", "") if isinstance(result, dict) else ""
        self._set_flow_action_pending(None, None)

        if action == "start":
            flow_index = self._flow_index_from_name(flow_name)
            self._apply_running_state(flow_index)
        elif action == "stop":
            self._stop_current_flow()

    def _on_flow_control_failed(self, _flow_name, _action, message):
        self._set_flow_action_pending(None, None)
        self._set_start_btn_state("error")
        self._show_flow_control_warning(message or "PLC 指令发送失败")

    def _set_start_btn_state(self, state):
        if not self.start_btn:
            return
        self._loading_timer.stop()
        self._loading_dot_step = 0
        self.start_btn.setEnabled(state != "disabled")
        self.start_btn.setProperty("state", state)

        if state == "loading":
            self.start_btn.setText("停止中" if self._pending_flow_action == "stop" else "启动中")
            self._loading_timer.start(280)
        elif state == "error":
            self.start_btn.setText("停止失败" if self._pending_flow_action == "stop" else "启动失败")
        else:
            self.start_btn.setText(self._start_btn_base_text)

        # 刷新动态属性对应的 QSS
        self.start_btn.style().unpolish(self.start_btn)
        self.start_btn.style().polish(self.start_btn)
        self.start_btn.update()

    def _handle_start_btn_click(self):
        if self._pending_flow_action:
            return

        if self._is_process_running:
            flow_name = self._get_running_flow_name()
            if flow_name:
                self.vm.stop_flow(flow_name)
            return

        flow_name = self._get_current_flow_name()
        if flow_name:
            self.vm.start_flow(flow_name)

    def _handle_emergency_stop_click(self):
        if self._pending_flow_action:
            return

        flow_name = self._get_running_flow_name() if self._is_process_running else self._get_current_flow_name()
        if flow_name:
            self.vm.stop_flow(flow_name)

    def _set_flow_nodes_status(self, status, flow_index=None):
        if not self.flow_stack or self.flow_stack.count() == 0:
            return

        if flow_index is None:
            flow_index = self.flow_stack.currentIndex()

        if flow_index < 0 or flow_index >= self.flow_stack.count():
            return

        flow_canvas = self.flow_stack.widget(flow_index)
        if flow_canvas is None:
            return

        for node in flow_canvas.findChildren(ProcessCard):
            node.set_status(status)

    def _apply_running_state(self, flow_index=None):
        running_index = flow_index if flow_index is not None else (self.flow_stack.currentIndex() if self.flow_stack else -1)
        self._is_process_running = True
        self._running_stage_index = running_index if running_index >= 0 else None
        self._start_btn_base_text = "停止流程"
        self._set_start_btn_state("default")
        self._set_flow_nodes_status("开启", self._running_stage_index)
        self._set_stage_cards_running(self._running_stage_index)

    def _stop_current_flow(self):
        running_index = self._running_stage_index
        self._is_process_running = False
        self._running_stage_index = None
        self._start_btn_base_text = "启动流程"
        self._set_start_btn_state("default")
        self._set_flow_nodes_status("停止", running_index)
        self._set_stage_cards_running(None)

    def _update_start_btn_loading_text(self):
        if not self.start_btn or self.start_btn.property("state") != "loading":
            return
        dots = "." * ((self._loading_dot_step % 3) + 1)
        prefix = "停止中" if self._pending_flow_action == "stop" else "启动中"
        self.start_btn.setText(f"{prefix}{dots}")
        self._loading_dot_step += 1

    def _set_stage_cards_running(self, running_index):
        for idx, card in enumerate(self.stage_cards):
            card.set_running(idx == running_index)

    def _set_active_stage_card(self, index):
        for idx, card in enumerate(self.stage_cards):
            card.set_selected(idx == index)
        
        # 切换流程显示
        if index < self.flow_stack.count():
            self.flow_stack.setCurrentIndex(index)

    def _create_card(self, title):
        """创建统一风格的卡片容器，并附带标题。"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #1A1F26;
                border-radius: 16px;
                border: 1px solid #2A3038;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold; border: none;")
        layout.addWidget(title_label)
        
        return card

    def _update_time(self):
        """刷新右上角时间显示。"""
        current_time = QDateTime.currentDateTime().toString("yyyy/M/d  HH:mm:ss")
        self.time_label.setText(current_time)
        
    def eventFilter(self, source, event):
        """监听 logo 点击，识别隐藏入口触发手势。

        逻辑为 5 秒内累计点击 3 次即触发 `secret_triggered` 信号，
        由外部决定是否进入运维或其他隐藏页面。
        """
        if source is self.logo_label and event.type() == QEvent.Type.MouseButtonPress:
            current_time = time.time()
            self.click_times.append(current_time)
            
            # 只保留最近 5 秒内的点击时间，形成一个滑动窗口。
            self.click_times = [t for t in self.click_times if current_time - t <= 5.0]
            
            if len(self.click_times) >= 3:
                # 触发后立即清空，避免后续一次点击继续误触发。
                self.click_times = []
                self.secret_triggered.emit()
                
        return super().eventFilter(source, event)
