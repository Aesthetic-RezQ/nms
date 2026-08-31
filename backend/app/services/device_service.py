from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, update
from app.models.device import Device
from app.models.category import Category
from app.models.group import DeviceGroup
from app.models.location import Location
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceListFilter
from app.core.exceptions import DuplicateException, NotFoundException, ValidationException
from uuid import UUID
import math
import csv
import io
from typing import Optional

class DeviceService:
    @staticmethod
    async def get_all(db: AsyncSession, page: int = 1, page_size: int = 10, filters: Optional[DeviceListFilter] = None):
        query = select(
            Device, 
            Category.name.label('category_name'), 
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
            
        await db.execute(update(Device).where(Device.parent_device_id == device_id).values(parent_device_id=None))
        await db.delete(device)
        await db.commit()

    @staticmethod
    async def bulk_import(db: AsyncSession, csv_content: str):
        reader = csv.DictReader(io.StringIO(csv_content))
        total = 0
        created = 0
        errors = []
        
        for row in reader:
            total += 1
            try:
                ip = row.get('ip_address')
                name = row.get('device_name')
                if not ip or not name:
                    errors.append(f"Row {total}: Missing required fields (device_name, ip_address)")
                    continue
                    
                ip_check = await db.execute(select(Device).where(Device.ip_address == ip))
                if ip_check.scalars().first():
                    errors.append(f"Row {total}: IP address {ip} already exists")
                    continue
                    
                device = Device(
                    device_name=name,
                    ip_address=ip,
                    hostname=row.get('hostname'),
                    description=row.get('description'),
                    current_status='UNKNOWN'
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
        writer = csv.DictWriter(output, fieldnames=['device_name', 'ip_address', 'hostname', 'category_name', 'group_name', 'location_name', 'current_status'])
        writer.writeheader()
        
        for device in devices:
            writer.writerow({
                'device_name': device['device_name'],
                'ip_address': device['ip_address'],
                'hostname': device['hostname'] or '',
                'category_name': device['category_name'] or '',
                'group_name': device['group_name'] or '',
                'location_name': device['location_name'] or '',
                'current_status': device['current_status']
            })
            
        return output.getvalue()
