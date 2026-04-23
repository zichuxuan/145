from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Material:
    """物料实体类"""
    id: Optional[int] = None
    material_code: str = ""
    material_name: str = ""
    material_type: Optional[str] = None
    material_spec: Optional[str] = None
    unit: Optional[str] = None
    description: Optional[str] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
