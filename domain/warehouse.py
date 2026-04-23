from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from decimal import Decimal

@dataclass
class Warehouse:
    """仓库实体类"""
    id: Optional[int] = None
    warehouse_code: str = ""
    warehouse_type: str = ""
    warehouse_name: str = ""
    warehouse_location: str = ""
    person_in_charge: Optional[str] = None
    contact_phone: Optional[str] = None
    warehouse_capacity: Optional[Decimal] = None
    capacity_unit: str = "平方米"
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
