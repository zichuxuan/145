"""智能生产模块的常量定义与配置 Schema 库。

该文件包含了工作流编辑器（远程控制画布）和配置表单中所需的所有常量数据。
主要包括下拉选项配置、设备配置字典、以及决定画布渲染和数据提取的 NODE_LIBRARY 与 NODE_SCHEMAS。
"""

import copy

WORKFLOW_TYPE_OPTIONS = [
    ("主动流程", "ACTIVE_PROCESS"),
    ("监控流程", "MONITORING_PROCESS"),
]

OUTPUT_PROPERTY_OPTIONS = ["状态", "完成信号", "告警信号", "结果输出"]
ACTION_OPTIONS = ["启动", "停止", "暂停", "复位"]
MESSAGE_TYPE_OPTIONS = ["系统消息", "告警消息", "提示消息"]
JUDGMENT_PROPERTY_OPTIONS = ["状态", "完成信号", "告警信号", "结果输出"]
JUDGMENT_OPERATOR_OPTIONS = ["等于", "不等于", "大于", "大于等于", "小于", "小于等于", "包含"]
JUDGMENT_LOGIC_OPTIONS = ["且", "或"]
VISIBILITY_OPTIONS = [("显示", True), ("隐藏", False)]

DEVICE_SAMPLE_COUNTS = {
    "screw_conveyor": 3,
    "belt_conveyor": 3,
    "chain_conveyor": 3,
    "vibrating_feeder": 2,
    "blower": 2,
    "smart_sorter": 2,
    "drum_screen": 2,
    "label_remover": 2,
    "crusher": 2,
    "baler": 2,
    "hopper": 3,
    "smart_hopper": 3,
}

# 节点类型库配置：定义了画布中可用节点的元数据
#   label: 节点在 UI 上的显示名称
#   group: 节点所属的分组，用于节点选择弹窗分类
#   accent: 节点在画布上的左侧边框及部分高亮颜色
NODE_LIBRARY = {
    "serial": {"label": "串行", "group": "事件", "accent": "#38BDF8"},
    "message": {"label": "消息", "group": "事件", "accent": "#38BDF8"},
    "judgment": {"label": "判断", "group": "网关", "accent": "#F59E0B"},
    "loop": {"label": "循环", "group": "网关", "accent": "#A855F7"},
    "wait": {"label": "等待", "group": "网关", "accent": "#64748B"},
    "screw_conveyor": {"label": "螺旋输送机", "group": "输送设备", "accent": "#10B981"},
    "belt_conveyor": {"label": "皮带输送机", "group": "输送设备", "accent": "#10B981"},
    "chain_conveyor": {"label": "板链输送机", "group": "输送设备", "accent": "#10B981"},
    "vibrating_feeder": {"label": "震动给料机", "group": "输送设备", "accent": "#10B981"},
    "blower": {"label": "吹瓶风机", "group": "输送设备", "accent": "#10B981"},
    "smart_sorter": {"label": "智能光选机", "group": "分选设备", "accent": "#3B82F6"},
    "drum_screen": {"label": "滚筒筛", "group": "分选设备", "accent": "#3B82F6"},
    "label_remover": {"label": "脱标机", "group": "处理设备", "accent": "#F97316"},
    "crusher": {"label": "破碎机", "group": "处理设备", "accent": "#F97316"},
    "baler": {"label": "压包机", "group": "处理设备", "accent": "#F97316"},
    "hopper": {"label": "普通料仓", "group": "存储设备", "accent": "#EF4444"},
    "smart_hopper": {"label": "智能料仓", "group": "存储设备", "accent": "#EF4444"},
}

GROUP_ORDER = ["事件", "网关", "输送设备", "分选设备", "处理设备", "存储设备"]

# 节点配置的字段 Schema：每个节点类型对应的弹窗表单字段定义。
# 每个列表元素代表一个字段：
#   key: 字典中保存的值键名
#   label: 在配置弹窗中的显示名称
#   type: 表单控件类型 (text, select, textarea, number)
#   default: 默认值
#   options (可选): 当 type 为 select 时的选项列表
#   min/max (可选): 当 type 为 number 时的范围
NODE_SCHEMAS = {
    "serial": [
        {"key": "name", "label": "串行名称", "type": "text", "default": "串行事件"},
        {"key": "output_property", "label": "输出属性", "type": "select", "options": OUTPUT_PROPERTY_OPTIONS, "default": "状态"},
    ],
    "message": [
        {"key": "message_title", "label": "消息标题", "type": "text", "default": ""},
        {"key": "message_content", "label": "消息内容", "type": "textarea", "default": ""},
        {"key": "message_type", "label": "消息类型", "type": "select", "options": MESSAGE_TYPE_OPTIONS, "default": "系统消息"},
    ],
    "judgment": [
        {"key": "condition_name", "label": "判断名称", "type": "text", "default": "判断节点"},
        {"key": "condition_expression", "label": "条件表达式", "type": "textarea", "default": ""},
        {"key": "yes_label", "label": "是分支文案", "type": "text", "default": "当满足时"},
        {"key": "no_label", "label": "否分支文案", "type": "text", "default": "否则"},
    ],
    "loop": [
        {"key": "loop_name", "label": "循环名称", "type": "text", "default": "循环节点"},
        {"key": "loop_count", "label": "循环次数", "type": "number", "default": 1, "min": 1, "max": 999},
        {"key": "exit_condition", "label": "退出条件", "type": "textarea", "default": ""},
    ],
    "wait": [
        {"key": "wait_seconds", "label": "等待时长（秒）", "type": "number", "default": 5, "min": 1, "max": 9999},
        {"key": "output_property", "label": "输出属性", "type": "select", "options": OUTPUT_PROPERTY_OPTIONS, "default": "状态"},
    ],
    "screw_conveyor": [
        {"key": "device_name", "label": "选择设备", "type": "select", "options": ["螺旋输送机-01", "螺旋输送机-02", "螺旋输送机-03"], "default": "螺旋输送机-01"},
        {"key": "action", "label": "执行动作", "type": "select", "options": ACTION_OPTIONS, "default": "启动"},
        {"key": "output_property", "label": "输出属性", "type": "select", "options": OUTPUT_PROPERTY_OPTIONS, "default": "状态"},
    ],
    "belt_conveyor": [
        {"key": "device_name", "label": "选择设备", "type": "select", "options": ["皮带输送机-01", "皮带输送机-02", "皮带输送机-03"], "default": "皮带输送机-01"},
        {"key": "action", "label": "执行动作", "type": "select", "options": ACTION_OPTIONS, "default": "启动"},
        {"key": "output_property", "label": "输出属性", "type": "select", "options": OUTPUT_PROPERTY_OPTIONS, "default": "状态"},
    ],
    "chain_conveyor": [
        {"key": "device_name", "label": "选择设备", "type": "select", "options": ["板链输送机-01", "板链输送机-02", "板链输送机-03"], "default": "板链输送机-01"},
        {"key": "action", "label": "执行动作", "type": "select", "options": ACTION_OPTIONS, "default": "启动"},
        {"key": "output_property", "label": "输出属性", "type": "select", "options": OUTPUT_PROPERTY_OPTIONS, "default": "状态"},
    ],
    "vibrating_feeder": [
        {"key": "device_name", "label": "选择设备", "type": "select", "options": ["震动给料机-01", "震动给料机-02"], "default": "震动给料机-01"},
        {"key": "action", "label": "执行动作", "type": "select", "options": ACTION_OPTIONS, "default": "启动"},
        {"key": "output_property", "label": "输出属性", "type": "select", "options": OUTPUT_PROPERTY_OPTIONS, "default": "状态"},
    ],
    "blower": [
        {"key": "device_name", "label": "选择设备", "type": "select", "options": ["吹瓶风机-01", "吹瓶风机-02"], "default": "吹瓶风机-01"},
        {"key": "action", "label": "执行动作", "type": "select", "options": ACTION_OPTIONS, "default": "启动"},
        {"key": "output_property", "label": "输出属性", "type": "select", "options": OUTPUT_PROPERTY_OPTIONS, "default": "状态"},
    ],
    "smart_sorter": [
        {"key": "device_name", "label": "选择设备", "type": "select", "options": ["智能光选机-01", "智能光选机-02"], "default": "智能光选机-01"},
        {"key": "action", "label": "执行动作", "type": "select", "options": ACTION_OPTIONS, "default": "启动"},
        {"key": "output_property", "label": "输出属性", "type": "select", "options": OUTPUT_PROPERTY_OPTIONS, "default": "状态"},
    ],
    "drum_screen": [
        {"key": "device_name", "label": "选择设备", "type": "select", "options": ["滚筒筛-01", "滚筒筛-02"], "default": "滚筒筛-01"},
        {"key": "action", "label": "执行动作", "type": "select", "options": ACTION_OPTIONS, "default": "启动"},
        {"key": "output_property", "label": "输出属性", "type": "select", "options": OUTPUT_PROPERTY_OPTIONS, "default": "状态"},
    ],
    "label_remover": [
        {"key": "device_name", "label": "选择设备", "type": "select", "options": ["脱标机-01", "脱标机-02"], "default": "脱标机-01"},
        {"key": "action", "label": "执行动作", "type": "select", "options": ACTION_OPTIONS, "default": "启动"},
        {"key": "output_property", "label": "输出属性", "type": "select", "options": OUTPUT_PROPERTY_OPTIONS, "default": "状态"},
    ],
    "crusher": [
        {"key": "device_name", "label": "选择设备", "type": "select", "options": ["破碎机-01", "破碎机-02"], "default": "破碎机-01"},
        {"key": "action", "label": "执行动作", "type": "select", "options": ACTION_OPTIONS, "default": "启动"},
        {"key": "output_property", "label": "输出属性", "type": "select", "options": OUTPUT_PROPERTY_OPTIONS, "default": "状态"},
    ],
    "baler": [
        {"key": "device_name", "label": "选择设备", "type": "select", "options": ["压包机-01", "压包机-02"], "default": "压包机-01"},
        {"key": "action", "label": "执行动作", "type": "select", "options": ACTION_OPTIONS, "default": "启动"},
        {"key": "output_property", "label": "输出属性", "type": "select", "options": OUTPUT_PROPERTY_OPTIONS, "default": "状态"},
    ],
    "hopper": [
        {"key": "device_name", "label": "选择设备", "type": "select", "options": ["普通料仓-01", "普通料仓-02", "普通料仓-03"], "default": "普通料仓-01"},
        {"key": "action", "label": "执行动作", "type": "select", "options": ACTION_OPTIONS, "default": "启动"},
        {"key": "output_property", "label": "输出属性", "type": "select", "options": OUTPUT_PROPERTY_OPTIONS, "default": "状态"},
    ],
    "smart_hopper": [
        {"key": "device_name", "label": "选择设备", "type": "select", "options": ["智能料仓-01", "智能料仓-02", "智能料仓-03"], "default": "智能料仓-01"},
        {"key": "action", "label": "执行动作", "type": "select", "options": ACTION_OPTIONS, "default": "启动"},
        {"key": "output_property", "label": "输出属性", "type": "select", "options": OUTPUT_PROPERTY_OPTIONS, "default": "状态"},
    ],
}

COMMON_NODE_SCHEMA_FIELDS = [
    {
        "key": "is_visible",
        "label": "是否显示",
        "type": "select",
        "options": VISIBILITY_OPTIONS,
        "default": True,
    }
]


def get_node_schema(node_type):
    """返回节点类型的完整配置 Schema。

    在各节点专有字段后统一追加通用字段，确保节点弹窗和默认配置保持一致。
    """
    schema = copy.deepcopy(NODE_SCHEMAS.get(node_type, []))
    schema.extend(copy.deepcopy(COMMON_NODE_SCHEMA_FIELDS))
    return schema
