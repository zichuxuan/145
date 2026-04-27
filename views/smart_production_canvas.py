import copy
from functools import partial
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QPushButton,
    QLabel,
    QScrollArea,
    QMessageBox,
    QDialog,
)
from .smart_production_constants import (
    NODE_LIBRARY,
)
from .smart_production_utils import (
    create_default_workflow_detail,
    clear_layout,
    get_node_summary,
    create_node,
    get_node_label,
)
from .smart_production_dialogs import (
    WorkflowNodePickerDialog,
    WorkflowNodeConfigDialog,
)

class MergeUpwardConnector(QWidget):
    """判断节点 "否则" 分支的末尾向上折返连线。
    
    使用 QPainter 绘制表示分支汇合的连线：向右延伸 -> 向上折转 -> 向右延伸，
    末尾带一个蓝色圆点，模拟与主线的汇合。
    """
    def __init__(self, scale_func, up_distance, parent=None):
        super().__init__(parent)
        self._scale_func = scale_func
        self.up_distance = up_distance
        self.setMinimumWidth(self._scaled(100))
        self.setStyleSheet("background: transparent;")

    def _scaled(self, value):
        return self._scale_func(value)

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        line_pen = QPen(QColor("#007AFF"))
        line_pen.setWidth(max(1, self._scaled(2)))
        painter.setPen(line_pen)

        width = self.width()
        height = self.height()
        
        start_x = 0
        start_y = height // 2

        turn_x = self._scaled(36)

        target_y = start_y - self.up_distance

        end_x = width - self._scaled(16)

        painter.drawLine(start_x, start_y, turn_x, start_y)
        painter.drawLine(turn_x, start_y, turn_x, target_y)
        painter.drawLine(turn_x, target_y, end_x, target_y)

        dot_radius = self._scaled(4)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#007AFF"))
        painter.drawEllipse(end_x - dot_radius, target_y - dot_radius, dot_radius * 2, dot_radius * 2)


class JudgmentNodeWidget(QFrame):
    """自定义判断节点 UI 组件，呈现左右拼接的卡片样式，带有两个分支出口。"""
    def __init__(self, node, scale_func, edit_cb, delete_cb, parent=None):
        super().__init__(parent)
        self._scale_func = scale_func
        self.node = node
        self.edit_cb = edit_cb
        self.delete_cb = delete_cb
        self.setFixedSize(self._scaled(260), self._scaled(120))
        self.setStyleSheet("background: transparent; border: none;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(self._scaled(90), self._scaled(10), self._scaled(20), self._scaled(10))
        
        config = self.node.get("config", {})
        yes_label = config.get("yes_label", "当满足时")
        no_label = config.get("no_label", "否则")
        
        self.lbl_yes = QLabel(yes_label)
        self.lbl_yes.setStyleSheet(f"color: white; font-size: {self._scaled(14)}px; font-weight: bold;")
        self.lbl_yes.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        self.lbl_no = QLabel(no_label)
        self.lbl_no.setStyleSheet(f"color: white; font-size: {self._scaled(14)}px; font-weight: bold;")
        self.lbl_no.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(self._scaled(8))
        btn_layout.addStretch()
        
        edit_btn = QPushButton("编辑")
        delete_btn = QPushButton("删除")
        edit_btn.setFixedSize(self._scaled(40), self._scaled(24))
        delete_btn.setFixedSize(self._scaled(40), self._scaled(24))
        
        btn_style = f"background-color: rgba(255,255,255,0.12); color: white; border-radius: {self._scaled(4)}px; font-size: {self._scaled(12)}px;"
        del_btn_style = f"background-color: rgba(239,68,68,0.12); color: #F87171; border-radius: {self._scaled(4)}px; font-size: {self._scaled(12)}px;"
        edit_btn.setStyleSheet(btn_style)
        delete_btn.setStyleSheet(del_btn_style)
        
        edit_btn.clicked.connect(self.edit_cb)
        delete_btn.clicked.connect(self.delete_cb)
        
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        
        layout.addWidget(self.lbl_yes)
        layout.addStretch()
        layout.addWidget(self.lbl_no)
        layout.addLayout(btn_layout)

    def _scaled(self, value):
        return self._scale_func(value)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        radius = self._scaled(12)
        left_width = self._scaled(80)
        
        # Draw right part (dark gray)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#2A2F3A"))
        painter.drawRoundedRect(0, 0, width - self._scaled(10), height, radius, radius)
        
        # Draw left part (orange)
        painter.setBrush(QColor("#F59E0B"))
        # Draw a rounded rect for left part
        painter.drawRoundedRect(0, 0, left_width, height, radius, radius)
        # Fill the right corners of the left part to make it flush with the right part
        painter.drawRect(left_width - radius, 0, radius, height)
        
        # Draw "判断" text in left part
        painter.setPen(QColor("white"))
        font = painter.font()
        font.setPixelSize(self._scaled(18))
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(0, 0, left_width, height, Qt.AlignmentFlag.AlignCenter, "判断")

        dot_radius = self._scaled(4)
        dot_x = width - self._scaled(10)

        top_y = self._scaled(24)
        bottom_y = self._scaled(88)
        
        painter.setBrush(QColor("#007AFF"))
        painter.drawEllipse(dot_x - dot_radius, top_y - dot_radius, dot_radius * 2, dot_radius * 2)
        painter.drawEllipse(dot_x - dot_radius, bottom_y - dot_radius, dot_radius * 2, dot_radius * 2)

        line_pen = QPen(QColor("#007AFF"))
        line_pen.setWidth(max(1, self._scaled(2)))
        painter.setPen(line_pen)
        painter.drawLine(width - self._scaled(10), top_y, width, top_y)
        painter.drawLine(width - self._scaled(10), bottom_y, width, bottom_y)


class RootJudgmentNodeWrapper(QWidget):
    """根判断节点的包装容器。

    使用自定义绘制补齐主线的水平连线；“否则”分支独立连接到结束节点。
    """

    def __init__(self, node, sequence, index, scale_func, edit_cb, delete_cb, build_seq_func, parent=None):
        super().__init__(parent)
        self._scale_func = scale_func
        self.setStyleSheet("background: transparent;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.judgment_card = JudgmentNodeWidget(node, scale_func, edit_cb, delete_cb)
        layout.addWidget(self.judgment_card, alignment=Qt.AlignmentFlag.AlignTop)

        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        spacer = QWidget()
        spacer.setFixedHeight(self._scaled(44))
        right_layout.addWidget(spacer)

        branch_layout = QHBoxLayout()
        branch_layout.setContentsMargins(0, 0, 0, 0)
        branch_layout.setSpacing(0)

        no_branch_seq = node.setdefault("no_branch", [])
        self.no_branch_widget = build_seq_func(no_branch_seq, is_root=False)
        branch_layout.addWidget(self.no_branch_widget, alignment=Qt.AlignmentFlag.AlignTop)

        self.no_branch_end = QLabel("结束")
        end_size = self._scaled(88)
        self.no_branch_end.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_branch_end.setFixedSize(end_size, end_size)
        self.no_branch_end.setStyleSheet(
            f"background-color: #DC2626; color: white; border-radius: {end_size // 2}px; "
            f"font-size: {self._scaled(24)}px; font-weight: 600;"
        )
        branch_layout.addWidget(self.no_branch_end, alignment=Qt.AlignmentFlag.AlignTop)

        right_layout.addLayout(branch_layout)
        right_layout.addStretch()

        layout.addWidget(right_container)

    def _scaled(self, value):
        return self._scale_func(value)

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        line_pen = QPen(QColor("#007AFF"))
        line_pen.setWidth(max(1, self._scaled(2)))
        painter.setPen(line_pen)

        start_x = self.judgment_card.width()
        top_y = self._scaled(24)
        end_x = self.width()

        painter.drawLine(start_x, top_y, end_x, top_y)


class WorkflowCanvasEditor(QWidget):
    """远程控制工作流可视化编辑器核心画布。
    
    采用完全基于 PyQt Layout (QHBoxLayout/QVBoxLayout) 的形式渲染流程，
    没有使用传统的连线引擎，而是通过递归布局结构展现主线、分支与循环。
    提供缩放、节点编辑/增删及全屏切换功能。
    """
    fullscreen_requested = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.workflow_detail = create_default_workflow_detail()
        self.zoom_factor = 1.0
        self.zoom_step = 0.1
        self.min_zoom_factor = 0.5
        self.max_zoom_factor = 2.0
        self.is_fullscreen_mode = False
        self.setStyleSheet("background-color: transparent;")
        self._init_ui()
        self.render_canvas()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        toolbar = QFrame()
        toolbar.setStyleSheet(
            """
            QFrame {
                background-color: rgba(255,255,255,0.04);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 16px;
            }
            """
        )
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(16, 12, 16, 12)
        toolbar_layout.setSpacing(10)

        self.fullscreen_btn = QPushButton("全屏")
        self.fullscreen_btn.setFixedSize(120, 42)
        self.fullscreen_btn.clicked.connect(self._toggle_fullscreen_requested)
        toolbar_layout.addWidget(self.fullscreen_btn)

        toolbar_layout.addStretch()

        self.zoom_out_btn = QPushButton("-")
        self.zoom_out_btn.setFixedSize(44, 42)
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        toolbar_layout.addWidget(self.zoom_out_btn)

        self.zoom_label = QLabel("100%")
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.zoom_label.setFixedWidth(76)
        self.zoom_label.setStyleSheet("color: white; font-size: 16px; font-weight: 600;")
        toolbar_layout.addWidget(self.zoom_label)

        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.setFixedSize(44, 42)
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        toolbar_layout.addWidget(self.zoom_in_btn)

        self.zoom_reset_btn = QPushButton("重置")
        self.zoom_reset_btn.setFixedSize(88, 42)
        self.zoom_reset_btn.clicked.connect(self.reset_zoom)
        toolbar_layout.addWidget(self.zoom_reset_btn)
        layout.addWidget(toolbar)

        button_style = (
            "QPushButton {"
            "background-color: rgba(255,255,255,0.1);"
            "color: white;"
            "border-radius: 10px;"
            "border: 1px solid rgba(255,255,255,0.16);"
            "font-size: 16px;"
            "font-weight: 500;"
            "}"
            "QPushButton:disabled { color: rgba(255,255,255,0.35); background-color: rgba(255,255,255,0.04); }"
        )
        for btn in (self.fullscreen_btn, self.zoom_out_btn, self.zoom_in_btn, self.zoom_reset_btn):
            btn.setStyleSheet(button_style)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("QScrollArea { background-color: #0B0E14; border: none; }")
        layout.addWidget(self.scroll_area)

        self.canvas_shell = QWidget()
        self.canvas_shell.setStyleSheet("background-color: #0B0E14;")
        self.canvas_shell_layout = QVBoxLayout(self.canvas_shell)
        self.canvas_shell_layout.setContentsMargins(0, 0, 0, 0)
        self.canvas_shell_layout.setSpacing(0)

        self.canvas_widget = QWidget()
        self.canvas_widget.setStyleSheet("background-color: #0B0E14;")
        self.canvas_layout = QVBoxLayout(self.canvas_widget)
        self.canvas_layout.setContentsMargins(40, 30, 40, 30)
        self.canvas_layout.setSpacing(28)
        self.canvas_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.canvas_shell_layout.addWidget(self.canvas_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setWidget(self.canvas_shell)
        self._refresh_zoom_controls()

    def set_workflow_detail(self, workflow_detail):
        if not isinstance(workflow_detail, dict):
            self.workflow_detail = create_default_workflow_detail()
        else:
            self.workflow_detail = copy.deepcopy(workflow_detail)
            if not isinstance(self.workflow_detail.get("sequence"), list):
                self.workflow_detail["sequence"] = []
        self.render_canvas()

    def get_workflow_detail(self):
        return copy.deepcopy(self.workflow_detail)

    def get_zoom_factor(self):
        return float(self.zoom_factor)

    def set_zoom_factor(self, zoom_factor):
        """设置画布的缩放比例。
        
        基于新比例触发全局重新渲染，以便使用 self._scaled 函数按新因子绘制大小。
        """
        clamped = max(self.min_zoom_factor, min(self.max_zoom_factor, float(zoom_factor)))
        if abs(clamped - self.zoom_factor) < 0.001:
            self._refresh_zoom_controls()
            return
        self.zoom_factor = clamped
        self._refresh_zoom_controls()
        self.render_canvas()

    def zoom_in(self):
        self.set_zoom_factor(self.zoom_factor + self.zoom_step)

    def zoom_out(self):
        self.set_zoom_factor(self.zoom_factor - self.zoom_step)

    def reset_zoom(self):
        self.set_zoom_factor(1.0)

    def set_fullscreen_mode(self, is_fullscreen):
        self.is_fullscreen_mode = bool(is_fullscreen)
        self.fullscreen_btn.setText("退出全屏" if self.is_fullscreen_mode else "全屏")

    def _toggle_fullscreen_requested(self):
        self.fullscreen_requested.emit(not self.is_fullscreen_mode)

    def _refresh_zoom_controls(self):
        self.zoom_label.setText(f"{int(round(self.zoom_factor * 100))}%")
        self.zoom_out_btn.setEnabled(self.zoom_factor > self.min_zoom_factor + 0.001)
        self.zoom_in_btn.setEnabled(self.zoom_factor < self.max_zoom_factor - 0.001)
        self.zoom_reset_btn.setEnabled(abs(self.zoom_factor - 1.0) > 0.001)

    def _scaled(self, value):
        """根据当前缩放系数换算像素值。
        
        通过该方法实现全部尺寸、间距、字体大小的联动缩放。
        
        Args:
            value (int/float): 基准大小（1.0 缩放比下的大小）。
        Returns:
            int: 缩放后的整型像素大小（至少为 1）。
        """
        return max(1, int(round(value * self.zoom_factor)))

    def render_canvas(self):
        """完全重新渲染工作流画布。
        
        清空整个容器的子布局并从 workflow_detail 中提取根 sequence
        递归地构建整棵组件树。
        """
        clear_layout(self.canvas_layout)

        hint = QLabel("远程控制")
        hint.setStyleSheet(
            f"color: rgba(255,255,255,0.88); font-size: {self._scaled(22)}px; font-weight: 600;"
        )
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.canvas_layout.addWidget(hint)

        root_widget = self._build_sequence_widget(self.workflow_detail["sequence"], is_root=True)
        self.canvas_layout.addWidget(root_widget, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.canvas_layout.addStretch()
        self.canvas_widget.adjustSize()
        self.canvas_shell.adjustSize()

    def _build_sequence_widget(self, sequence, is_root=False):
        """将一个流程节点序列转换为水平的 Qt 布局组件。
        
        Args:
            sequence (list): 包含节点配置的字典列表。
            is_root (bool): 是否是根流程。如果是，会在首尾渲染特殊的 开始/结束 标志。
        Returns:
            QWidget: 包含渲染好节点的容器。
        """
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(self._scaled(20), self._scaled(20), self._scaled(20), self._scaled(20))
        layout.setSpacing(self._scaled(18))
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        if is_root:
            layout.addWidget(self._create_endpoint("开始", "#059669"), alignment=Qt.AlignmentFlag.AlignTop)

        layout.addWidget(self._create_connector(sequence, 0), alignment=Qt.AlignmentFlag.AlignTop)

        for index, node in enumerate(sequence):
            layout.addWidget(self._create_node_container(sequence, index, node, is_root=is_root), alignment=Qt.AlignmentFlag.AlignTop)
            layout.addWidget(self._create_connector(sequence, index + 1), alignment=Qt.AlignmentFlag.AlignTop)

        if is_root:
            layout.addWidget(self._create_endpoint("结束", "#DC2626"), alignment=Qt.AlignmentFlag.AlignTop)

        return container

    def _create_endpoint(self, text, color):
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        size = self._scaled(88)
        label.setFixedSize(size, size)
        label.setStyleSheet(
            f"background-color: {color}; color: white; border-radius: {size // 2}px; "
            f"font-size: {self._scaled(24)}px; font-weight: 600;"
        )
        return label

    def _create_add_button(self, sequence, index):
        btn = QPushButton("+")
        button_size = self._scaled(48)
        btn.setFixedSize(button_size, button_size)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(
            (
                "QPushButton {"
                "background-color: #FFFFFF;"
                "color: #007AFF;"
                f"border-radius: {button_size // 2}px;"
                "border: 2px solid #FFFFFF;"
                f"font-size: {self._scaled(26)}px;"
                "font-weight: 700;"
                "}"
                "QPushButton:hover { background-color: #EAF3FF; color: #007AFF; }"
                "QPushButton:pressed { background-color: #D8E9FF; color: #0062CC; }"
            )
        )
        btn.clicked.connect(partial(self._add_node, sequence, index))
        return btn

    def _create_connector(self, sequence, index):
        connector = QWidget()
        layout = QHBoxLayout(connector)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(self._scaled(8))
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._create_connector_line())
        layout.addWidget(self._create_add_button(sequence, index))
        layout.addWidget(self._create_connector_line())
        return connector

    def _create_connector_line(self):
        line = QFrame()
        line.setFixedSize(self._scaled(36), max(1, self._scaled(2)))
        line.setStyleSheet("background-color: #007AFF; border: none;")
        return line

    def _create_node_container(self, sequence, index, node, is_root=False):
        node_type = node.get("type")
        if node_type == "judgment":
            return self._create_branching_node(sequence, index, node, is_root=is_root)
        if node_type == "loop":
            return self._create_loop_node(sequence, index, node)
        return self._create_standard_node(sequence, index, node)

    def _create_standard_node(self, sequence, index, node):
        meta = NODE_LIBRARY.get(node.get("type"), {})
        frame = QFrame()
        frame.setFixedWidth(self._scaled(220))
        frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.16);
                border-left: {max(2, self._scaled(4))}px solid {meta.get('accent', '#007AFF')};
                border-radius: {self._scaled(16)}px;
            }}
            """
        )
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(self._scaled(16), self._scaled(14), self._scaled(16), self._scaled(14))
        layout.setSpacing(self._scaled(10))

        title = QLabel(meta.get("label", node.get("type", "节点")))
        title.setStyleSheet(
            f"color: white; font-size: {self._scaled(20)}px; font-weight: 600; background: transparent; border: none;"
        )
        layout.addWidget(title)

        summary = QLabel(get_node_summary(node))
        summary.setWordWrap(True)
        summary.setStyleSheet(
            f"color: rgba(255,255,255,0.72); font-size: {self._scaled(15)}px; background: transparent; border: none;"
        )
        layout.addWidget(summary)

        actions = QHBoxLayout()
        actions.setSpacing(self._scaled(10))
        edit_btn = QPushButton("编辑")
        delete_btn = QPushButton("删除")
        edit_btn.setFixedHeight(self._scaled(34))
        delete_btn.setFixedHeight(self._scaled(34))
        edit_btn.setStyleSheet(
            f"background-color: rgba(255,255,255,0.12); color: white; border-radius: {self._scaled(10)}px; "
            f"border: 1px solid rgba(255,255,255,0.15); font-size: {self._scaled(14)}px;"
        )
        delete_btn.setStyleSheet(
            f"background-color: rgba(239,68,68,0.12); color: #F87171; border-radius: {self._scaled(10)}px; "
            f"border: 1px solid rgba(239,68,68,0.28); font-size: {self._scaled(14)}px;"
        )
        edit_btn.clicked.connect(partial(self._edit_node, node))
        delete_btn.clicked.connect(partial(self._delete_node, sequence, index))
        actions.addWidget(edit_btn)
        actions.addWidget(delete_btn)
        layout.addLayout(actions)
        return frame

    def _create_root_judgment_node(self, sequence, index, node):
        return RootJudgmentNodeWrapper(
            node,
            sequence,
            index,
            self._scaled,
            partial(self._edit_node, node),
            partial(self._delete_node, sequence, index),
            self._build_sequence_widget,
        )

    def _create_branching_node(self, sequence, index, node, is_root=False):
        """渲染分支/判断节点。"""
        if is_root:
            return self._create_root_judgment_node(sequence, index, node)
        wrapper = QFrame()
        wrapper.setStyleSheet("background: transparent; border: none;")
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(self._scaled(16))
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        top_card = self._create_standard_node(sequence, index, node)
        top_card.setFixedWidth(self._scaled(260))
        layout.addWidget(top_card, alignment=Qt.AlignmentFlag.AlignHCenter)

        branch_row = QHBoxLayout()
        branch_row.setSpacing(self._scaled(24))
        branch_row.addWidget(self._create_branch_panel(node, "yes_branch", node.get("config", {}).get("yes_label", "是")))
        branch_row.addWidget(self._create_branch_panel(node, "no_branch", node.get("config", {}).get("no_label", "否")))
        layout.addLayout(branch_row)

        merge = QLabel("分支汇合后继续主流程")
        merge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        merge.setStyleSheet(f"color: rgba(255,255,255,0.5); font-size: {self._scaled(14)}px;")
        layout.addWidget(merge)
        return wrapper

    def _create_loop_node(self, sequence, index, node):
        wrapper = QFrame()
        wrapper.setStyleSheet("background: transparent; border: none;")
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(self._scaled(16))
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        top_card = self._create_standard_node(sequence, index, node)
        top_card.setFixedWidth(self._scaled(260))
        layout.addWidget(top_card, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self._create_branch_panel(node, "body_branch", "循环体"), alignment=Qt.AlignmentFlag.AlignHCenter)

        footer = QLabel("循环体执行完成后回到循环节点")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet(f"color: rgba(255,255,255,0.5); font-size: {self._scaled(14)}px;")
        layout.addWidget(footer)
        return wrapper

    def _create_branch_panel(self, node, branch_key, title_text):
        sequence = node.setdefault(branch_key, [])
        panel = QFrame()
        panel.setStyleSheet(
            f"""
            QFrame {{
                background-color: rgba(255,255,255,0.04);
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: {self._scaled(16)}px;
            }}
            """
        )
        panel.setMinimumWidth(self._scaled(420))
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(self._scaled(16), self._scaled(14), self._scaled(16), self._scaled(14))
        layout.setSpacing(self._scaled(12))

        title = QLabel(title_text)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            f"color: white; font-size: {self._scaled(18)}px; font-weight: 600; border: none; background: transparent;"
        )
        layout.addWidget(title)

        layout.addWidget(self._build_sequence_widget(sequence, is_root=False))
        return panel

    def _add_node(self, sequence, index):
        picker = WorkflowNodePickerDialog(self)
        if picker.exec() != QDialog.DialogCode.Accepted or not picker.selected_type:
            return
        node = create_node(picker.selected_type)
        dialog = WorkflowNodeConfigDialog(picker.selected_type, node.get("config"), self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        node["config"] = dialog.get_config()
        sequence.insert(index, node)
        self.render_canvas()

    def _edit_node(self, node):
        dialog = WorkflowNodeConfigDialog(node.get("type"), node.get("config"), self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            node["config"] = dialog.get_config()
            self.render_canvas()

    def _delete_node(self, sequence, index):
        node = sequence[index]
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定删除节点“{get_node_label(node.get('type'))}”吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            sequence.pop(index)
            self.render_canvas()
