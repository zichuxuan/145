from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any, Dict

@dataclass
class DeviceModel:
    """设备型号实体类"""
    id: Optional[int] = None
    model_name: str = ""
    model_code: str = ""
    description: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class DeviceInstance:
    """设备实例实体类"""
    id: Optional[int] = None
    device_model_id: int = 0
    device_code: str = ""
    device_name: str = ""
    device_category: Optional[str] = None
    production_line: Optional[str] = None
    location: Optional[str] = None
    device_status: int = 0  # 0-离线, 1-在线, 2-运行中, 3-故障
    device_data: Optional[Dict[str, Any]] = None
    communication_protocol: Optional[str] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class DeviceAction:
    """设备动作实体类"""
    id: Optional[int] = None
    device_instance_id: int = 0
    action_name: str = ""
    action_command_params: Optional[Dict[str, Any]] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class DeviceLog:
    """设备日志实体类"""
    id: Optional[int] = None
    device_instance_id: int = 0
    log_level: str = ""  # INFO, WARN, ERROR, DEBUG
    event_type: str = ""
    log_summary: Optional[str] = None
    detailed_info: Optional[str] = None
    log_generated_time: Optional[datetime] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
