from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select, func, or_, update
from app.models.device import Device
from app.models.category import Category
from app.models.group import DeviceGroup
from app.models.location import Location
from app.models.incident import Incident
from app.models.maintenance import maintenance_devices
from app.models.monitoring_result import MonitoringResult
from app.models.notification_log import NotificationLog
from app.models.ping_timeout_log import PingTimeoutLog
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceListFilter
from app.core.exceptions import DuplicateException, NotFoundException, ValidationException
from uuid import UUID
import math
import csv
import io
import ipaddress
from typing import Optional

class DeviceService:
    @staticmethod
    async def get_all(db: AsyncSession, page: int = 1, page_size: int = 10, filters: Optional[DeviceListFilter] = None):
        query = select(
            Device, 
            Category.name.label('category_name'),
            Category.criticality.label('category_criticality'),
            Category.incident_enabled.label('category_incident_enabled'),
            Category.alert_enabled.label('category_alert_enabled'),
            Category.sla_enabled.label('category_sla_enabled'),
            DeviceGroup.name.label('group_name'), 
            Location.name.label('location_name')
        ).outerjoin(Category, Device.category_id == Category.id)\
         .outerjoin(DeviceGroup, Device.group_id == DeviceGroup.id)\
         .outerjoin(Location, Device.location_id == Location.id)
        
        count_query = select(func.count(Device.id))
        
        if filters:
            if filters.status:
                query = query.where(Device.current_status == filters.status)
                count_query = count_query.where(Device.current_status == filters.status)
            if filters.category_id:
                query = query.where(Device.category_id == filters.category_id)
                count_query = count_query.where(Device.category_id == filters.category_id)
            if filters.group_id:
                query = query.where(Device.group_id == filters.group_id)
                count_query = count_query.where(Device.group_id == filters.group_id)
            if filters.location_id:
                query = query.where(Device.location_id == filters.location_id)
                count_query = count_query.where(Device.location_id == filters.location_id)
            if filters.vlan_id:
                query = query.where(Device.vlan_id == filters.vlan_id)
                count_query = count_query.where(Device.vlan_id == filters.vlan_id)
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.where(or_(Device.device_name.ilike(search_term), Device.ip_address.ilike(search_term), Device.hostname.ilike(search_term)))
                count_query = count_query.where(or_(Device.device_name.ilike(search_term), Device.ip_address.ilike(search_term), Device.hostname.ilike(search_term)))
                
        result = await db.execute(count_query)
        total = result.scalar() or 0
        
        query = query.order_by(Device.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        
        data = []
        for row in result.all():
            device_dict = {c.name: getattr(row.Device, c.name) for c in row.Device.__table__.columns}
            device_dict['category_name'] = row.category_name
            device_dict['criticality'] = row.category_criticality or 'CRITICAL'
            device_dict['incident_enabled'] = row.category_incident_enabled if row.category_incident_enabled is not None else True
            device_dict['alert_enabled'] = row.category_alert_enabled if row.category_alert_enabled is not None else True
            device_dict['sla_enabled'] = row.category_sla_enabled if row.category_sla_enabled is not None else True
            device_dict['group_name'] = row.group_name
            device_dict['location_name'] = row.location_name
            data.append(device_dict)
            
        return {
            "data": data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if total > 0 else 0
        }

    @staticmethod
    async def get_by_id(db: AsyncSession, device_id: UUID):
        query = select(
            Device, 
            Category.name.label('category_name'),
            Category.criticality.label('category_criticality'),
            Category.incident_enabled.label('category_incident_enabled'),
            Category.alert_enabled.label('category_alert_enabled'),
            Category.sla_enabled.label('category_sla_enabled'),
            DeviceGroup.name.label('group_name'), 
            Location.name.label('location_name')
        ).outerjoin(Category, Device.category_id == Category.id)\
         .outerjoin(DeviceGroup, Device.group_id == DeviceGroup.id)\
         .outerjoin(Location, Device.location_id == Location.id)\
         .where(Device.id == device_id)
         
        result = await db.execute(query)
        row = result.first()
        if not row:
            raise NotFoundException("Device not found")
            
        device_dict = {c.name: getattr(row.Device, c.name) for c in row.Device.__table__.columns}
        device_dict['category_name'] = row.category_name
        device_dict['criticality'] = row.category_criticality or 'CRITICAL'
        device_dict['incident_enabled'] = row.category_incident_enabled if row.category_incident_enabled is not None else True
        device_dict['alert_enabled'] = row.category_alert_enabled if row.category_alert_enabled is not None else True
        device_dict['sla_enabled'] = row.category_sla_enabled if row.category_sla_enabled is not None else True
        device_dict['group_name'] = row.group_name
        device_dict['location_name'] = row.location_name
        return device_dict

    @staticmethod
    async def create(db: AsyncSession, data: DeviceCreate):
        result = await db.execute(select(Device).where(Device.ip_address == data.ip_address))
        if result.scalars().first():
            raise DuplicateException("IP address already exists")
            
        device = Device(**data.model_dump(exclude_unset=True))
        db.add(device)
        await db.commit()
        await db.refresh(device)
        return await DeviceService.get_by_id(db, device.id)

    @staticmethod
    async def update(db: AsyncSession, device_id: UUID, data: DeviceUpdate):
        result = await db.execute(select(Device).where(Device.id == device_id))
        device = result.scalars().first()
        if not device:
            raise NotFoundException("Device not found")
            
        if data.ip_address and data.ip_address != device.ip_address:
            ip_check = await db.execute(select(Device).where(Device.ip_address == data.ip_address))
            if ip_check.scalars().first():
                raise DuplicateException("IP address already exists")
                
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(device, key, value)
            
        await db.commit()
        return await DeviceService.get_by_id(db, device_id)

    @staticmethod
    async def delete(db: AsyncSession, device_id: UUID):
        result = await db.execute(select(Device).where(Device.id == device_id))
        device = result.scalars().first()
        if not device:
            raise NotFoundException("Device not found")

        await DeviceService._delete_device_records(db, device)
        await db.commit()

    @staticmethod
    async def _delete_device_records(db: AsyncSession, device: Device):
        """Remove device-owned records before deleting a device row."""
        device_id = device.id
        # Remove device-owned records explicitly. This keeps deletion reliable for
        # databases created before every foreign-key cascade was introduced.
        await db.execute(delete(PingTimeoutLog).where(PingTimeoutLog.device_id == device_id))
        await db.execute(delete(MonitoringResult).where(MonitoringResult.device_id == device_id))
        await db.execute(delete(maintenance_devices).where(maintenance_devices.c.device_id == device_id))
        await db.execute(
            update(NotificationLog)
            .where(NotificationLog.device_id == device_id)
            .values(device_id=None)
        )
        await db.execute(delete(Incident).where(Incident.device_id == device_id))
        await db.execute(update(Device).where(Device.parent_device_id == device_id).values(parent_device_id=None))
        await db.delete(device)

    @staticmethod
    async def bulk_delete(db: AsyncSession, device_ids: list[UUID]) -> int:
        unique_ids = list(dict.fromkeys(device_ids))
        result = await db.execute(select(Device).where(Device.id.in_(unique_ids)))
        devices = result.scalars().all()
        if len(devices) != len(unique_ids):
            raise NotFoundException("One or more selected devices were not found")

        for device in devices:
            await DeviceService._delete_device_records(db, device)

        await db.commit()
        return len(devices)

    @staticmethod
    async def _get_or_create_named_entity(db: AsyncSession, model, name: Optional[str], cache: dict):
        """Resolve a CSV name to a related record, creating it when necessary."""
        if not name:
            return None

        normalized_name = name.strip()
        if not normalized_name:
            return None

        cache_key = normalized_name.casefold()
        if cache_key in cache:
            return cache[cache_key]

        result = await db.execute(
            select(model).where(func.lower(model.name) == cache_key)
        )
        entity = result.scalars().first()
        if not entity:
            entity = model(name=normalized_name)
            db.add(entity)
            await db.flush()

        cache[cache_key] = entity
        return entity

    @staticmethod
    async def bulk_import(db: AsyncSession, csv_content: str):
        reader = csv.DictReader(io.StringIO(csv_content.lstrip("\ufeff")))
        total = 0
        created = 0
        errors = []
        category_cache = {}
        group_cache = {}
        location_cache = {}

        if not reader.fieldnames:
            return {
                "total": total,
                "created": created,
                "errors": ["CSV file must include a header row"],
            }
        
        for raw_row in reader:
            total += 1
            try:
                row = {
                    (key or "").strip().casefold(): (value or "").strip()
                    for key, value in raw_row.items()
                }
                ip = row.get('ip_address')
                name = row.get('device_name')
                if not ip or not name:
                    errors.append(f"Row {total}: Missing required fields (device_name, ip_address)")
                    continue

                try:
                    ipaddress.IPv4Address(ip)
                except ValueError:
                    errors.append(f"Row {total}: Invalid IPv4 address {ip}")
                    continue
                    
                ip_check = await db.execute(select(Device).where(Device.ip_address == ip))
                if ip_check.scalars().first():
                    errors.append(f"Row {total}: IP address {ip} already exists")
                    continue

                vlan_id = None
                if row.get('vlan_id'):
                    try:
                        vlan_id = int(row['vlan_id'])
                    except ValueError:
                        errors.append(f"Row {total}: VLAN ID must be a whole number")
                        continue

                category = await DeviceService._get_or_create_named_entity(
                    db,
                    Category,
                    row.get('category') or row.get('category_name'),
                    category_cache,
                )
                group = await DeviceService._get_or_create_named_entity(
                    db,
                    DeviceGroup,
                    row.get('group') or row.get('group_name'),
                    group_cache,
                )
                location = await DeviceService._get_or_create_named_entity(
                    db,
                    Location,
                    row.get('location') or row.get('location_name'),
                    location_cache,
                )
                    
                device = Device(
                    device_name=name,
                    ip_address=ip,
                    hostname=row.get('hostname') or None,
                    description=row.get('description') or None,
                    category_id=category.id if category else None,
                    group_id=group.id if group else None,
                    location_id=location.id if location else None,
                    vlan_id=vlan_id,
                    vlan_name=row.get('vlan_name') or None,
                    subnet=row.get('subnet') or None,
                    current_status='UNKNOWN',
                )
                db.add(device)
                created += 1
            except Exception as e:
                errors.append(f"Row {total}: {str(e)}")
                
        await db.commit()
        return {"total": total, "created": created, "errors": errors}

    @staticmethod
    async def export(db: AsyncSession, filters: Optional[DeviceListFilter] = None):
        result = await DeviceService.get_all(db, page=1, page_size=10000, filters=filters)
        devices = result['data']
        
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                'device_name', 'ip_address', 'hostname', 'category', 'group',
                'location', 'vlan_id', 'vlan_name', 'subnet', 'description',
                'current_status',
            ],
        )
        writer.writeheader()
        
        for device in devices:
            writer.writerow({
                'device_name': device['device_name'],
                'ip_address': device['ip_address'],
                'hostname': device['hostname'] or '',
                'category': device['category_name'] or '',
                'group': device['group_name'] or '',
                'location': device['location_name'] or '',
                'vlan_id': device['vlan_id'] or '',
                'vlan_name': device['vlan_name'] or '',
                'subnet': device['subnet'] or '',
                'description': device['description'] or '',
                'current_status': device['current_status'],
            })
            
        return output.getvalue()
