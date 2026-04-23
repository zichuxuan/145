from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any, Dict

@dataclass
class Workflow:
    """工作流实体类"""
    id: Optional[int] = None
    workflow_name: str = ""
    workflow_type: str = ""
    workflow_params: Optional[Dict[str, Any]] = None
    workflow_detail: Optional[Dict[str, Any]] = None
    conditions: Optional[Dict[str, Any]] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class WorkflowExecutionLog:
    """工作流执行日志实体类"""
    id: Optional[int] = None
    workflow_id: int = 0
    execution_status: str = ""
    error_message: Optional[str] = None
    frequency: Optional[str] = None
    communication_params: Optional[Dict[str, Any]] = None
    workflow_detail: Optional[Dict[str, Any]] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    execution_start_time: Optional[datetime] = None
    execution_end_time: Optional[datetime] = None
    created_at: Optional[datetime] = None
