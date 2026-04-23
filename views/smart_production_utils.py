"""智能生产模块的工具函数库。

该文件包含了 UI 布局清理、数据结构初始化、节点属性提取等帮助函数，
主要为智能生产配置页面及远程控制画布提供支持。
"""
import copy
from uuid import uuid4
from .smart_production_constants import (
    WORKFLOW_TYPE_OPTIONS,
    NODE_LIBRARY,
    NODE_SCHEMAS,
)

def clear_layout(layout):
    """递归清空给定的布局及其所有子组件。
    
    Args:
        layout (QLayout): 需要被清空的布局对象。
    """
    while layout.count():
        item = layout.takeAt(0)
        child_layout = item.layout()
        child_widget = item.widget()
        if child_layout is not None:
            clear_layout(child_layout)
        if child_widget is not None:
            child_widget.deleteLater()

def workflow_type_label(type_value):
    """根据工作流类型值获取其对应的中文显示标签。
    
    Args:
        type_value (str): 工作流的内部类型值（如 "PLATFORM_FEED"）。
        
    Returns:
        str: 对应的中文标签（如 "平台上料"）。未找到时返回传入的值。
    """
    for label, value in WORKFLOW_TYPE_OPTIONS:
        if value == type_value:
            return label
    return type_value or "-"

def build_default_config(node_type):
    """基于节点类型的 Schema 定义，构建包含默认值的配置字典。
    
    Args:
        node_type (str): 节点的类型标识（如 "message", "wait"）。
        
    Returns:
        dict: 包含各字段默认值的字典配置。
    """
    config = {}
    for field in NODE_SCHEMAS.get(node_type, []):
        config[field["key"]] = copy.deepcopy(field.get("default"))
    return config

def create_node(node_type):
    """创建一个带有唯一 ID 和默认配置的节点数据结构。
    
    对于特殊类型（如判断节点、循环节点），会自动初始化分支所需的列表结构。
    
    Args:
        node_type (str): 节点的类型标识。
        
    Returns:
        dict: 初始化后的节点字典对象。
    """
    node = {
        "id": uuid4().hex[:8],
        "type": node_type,
        "config": build_default_config(node_type),
    }
    if node_type == "judgment":
        node["yes_branch"] = []
        node["no_branch"] = []
    if node_type == "loop":
        node["body_branch"] = []
    return node

def create_default_workflow_detail():
    """创建一个默认的工作流详情数据结构。
    
    Returns:
        dict: 包含版本号及初始序列的工作流字典。
    """
    return {
        "version": 1,
        "sequence": [],
    }

def get_node_label(node_type):
    """获取节点类型在 UI 上的显示名称。
    
    Args:
        node_type (str): 节点类型标识。
        
    Returns:
        str: 节点中文名称。
    """
    return NODE_LIBRARY.get(node_type, {}).get("label", node_type)

def get_node_summary(node):
    """提取节点配置中的核心信息，作为摘要在画布上显示。
    
    Args:
        node (dict): 包含 "type" 和 "config" 的节点数据字典。
        
    Returns:
        str: 提取出的节点摘要文案。
    """
    config = node.get("config", {}) if isinstance(node, dict) else {}
    node_type = node.get("type", "") if isinstance(node, dict) else ""
    if node_type == "message":
        return config.get("message_title") or config.get("message_type") or "未配置"
    if node_type == "wait":
        seconds = config.get("wait_seconds")
        return f"等待 {seconds}s" if seconds else "未配置"
    if node_type == "judgment":
        return config.get("condition_expression") or "未配置条件"
    if node_type == "loop":
        count = config.get("loop_count")
        return f"循环 {count} 次" if count else "未配置"
    if config.get("device_name"):
        return f"{config.get('device_name')} / {config.get('action', '-') }"
    if config.get("name"):
        return config.get("name")
    return "点击编辑节点"

def extract_workflow_description(workflow):
    """从工作流数据中提取描述信息。
    
    优先从 "workflow_params" 中获取，若无则尝试从 "conditions" 获取。
    
    Args:
        workflow (dict): 包含工作流元数据的字典。
        
    Returns:
        str: 提取到的工作流描述文本。
    """
    if not isinstance(workflow, dict):
        return ""
    workflow_params = workflow.get("workflow_params") if isinstance(workflow.get("workflow_params"), dict) else {}
    conditions = workflow.get("conditions") if isinstance(workflow.get("conditions"), dict) else {}
    return workflow_params.get("description") or conditions.get("description") or ""
