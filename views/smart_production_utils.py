import copy
from uuid import uuid4
from .smart_production_constants import (
    WORKFLOW_TYPE_OPTIONS,
    NODE_LIBRARY,
    NODE_SCHEMAS,
)

def clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)
        child_layout = item.layout()
        child_widget = item.widget()
        if child_layout is not None:
            clear_layout(child_layout)
        if child_widget is not None:
            child_widget.deleteLater()

def workflow_type_label(type_value):
    for label, value in WORKFLOW_TYPE_OPTIONS:
        if value == type_value:
            return label
    return type_value or "-"

def build_default_config(node_type):
    config = {}
    for field in NODE_SCHEMAS.get(node_type, []):
        config[field["key"]] = copy.deepcopy(field.get("default"))
    return config

def create_node(node_type):
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
    return {
        "version": 1,
        "sequence": [],
    }

def get_node_label(node_type):
    return NODE_LIBRARY.get(node_type, {}).get("label", node_type)

def get_node_summary(node):
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
    if not isinstance(workflow, dict):
        return ""
    workflow_params = workflow.get("workflow_params") if isinstance(workflow.get("workflow_params"), dict) else {}
    conditions = workflow.get("conditions") if isinstance(workflow.get("conditions"), dict) else {}
    return workflow_params.get("description") or conditions.get("description") or ""
