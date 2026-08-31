from pydantic import BaseModel, IPvAnyAddress, field_validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime
import ipaddress

class DeviceCreate(BaseModel):
    device_name: str
    ip_address: str
    hostname: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    group_id: Optional[int] = None
    location_id: Optional[int] = None
    vlan_id: Optional[int] = None
    vlan_name: Optional[str] = None
    subnet: Optional[str] = None
    parent_device_id: Optional[UUID] = None
    monitoring_enabled: Optional[bool] = True
    monitoring_interval: Optional[int] = None
    ping_timeout: Optional[int] = None
    failure_threshold: Optional[int] = None
    recovery_threshold: Optional[int] = None

    @field_validator('ip_address')
    @classmethod
    def validate_ip(cls, v):
        ipaddress.IPv4Address(v)
        return v

class DeviceUpdate(BaseModel):
    device_name: Optional[str] = None
    ip_address: Optional[str] = None
    hostname: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    group_id: Optional[int] = None
    location_id: Optional[int] = None
    vlan_id: Optional[int] = None
    vlan_name: Optional[str] = None
    subnet: Optional[str] = None
    parent_device_id: Optional[UUID] = None
    monitoring_enabled: Optional[bool] = None
    monitoring_interval: Optional[int] = None
    ping_timeout: Optional[int] = None
    failure_threshold: Optional[int] = None
    recovery_threshold: Optional[int] = None

    @field_validator('ip_address')
    @classmethod
    def validate_ip(cls, v):
        if v is not None:
            ipaddress.IPv4Address(v)
        return v

class DeviceRead(BaseModel):
    id: UUID
    device_name: str
    ip_address: str
    hostname: Optional[str]
    description: Optional[str]
    category_id: Optional[int]
    group_id: Optional[int]
    location_id: Optional[int]
    vlan_id: Optional[int]
    vlan_name: Optional[str]
    subnet: Optional[str]
    parent_device_id: Optional[UUID]
    monitoring_enabled: bool
    monitoring_interval: Optional[int]
    ping_timeout: Optional[int]
    failure_threshold: Optional[int]
    recovery_threshold: Optional[int]
    current_status: str
    last_check: Optional[datetime]
    last_seen: Optional[datetime]
    last_up: Optional[datetime]
    last_down: Optional[datetime]
    current_latency: Optional[float]
    created_at: datetime
    updated_at: datetime
    
    category_name: Optional[str] = None
    group_name: Optional[str] = None
    location_name: Optional[str] = None
    parent_device_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class DeviceListFilter(BaseModel):
    status: Optional[str] = None
    category_id: Optional[int] = None
    group_id: Optional[int] = None
    location_id: Optional[int] = None
    vlan_id: Optional[int] = None
    search: Optional[str] = None

class DeviceBulkImportResult(BaseModel):
    total: int
    created: int
    errors: List[str]
