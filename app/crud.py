from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .models import Device, Stat
from .schemas import DeviceCreate, StatCreate
from datetime import datetime
from .tasks import analyze_device_stats, analyze_user_devices
from fastapi import HTTPException

# Создание нового устройства
def create_device(db: Session, device: DeviceCreate):
    try:
        db_device = Device(device_id=device.device_id, owner=device.owner)
        db.add(db_device)
        db.commit()
        db.refresh(db_device)
        return db_device
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Device with ID {device.device_id} already exists"
        )

# Создание новой записи статистики
def create_stat(db: Session, stat: StatCreate, device_id: int):
    db_stat = Stat(**stat.dict(), device_id=device_id)
    db.add(db_stat)
    db.commit()
    db.refresh(db_stat)
    return db_stat

# Получение всех записей статистики для устройства за определенный период
def get_stats_by_device(db: Session, device_id: int, start_time: datetime, end_time: datetime):
    return db.query(Stat).filter(
        Stat.device_id == device_id,
        Stat.timestamp >= start_time,
        Stat.timestamp <= end_time
    ).all()

# Запуск анализа статистики устройства
def start_device_analysis(db: Session, device_id: int, start_time: datetime, end_time: datetime):
    task = analyze_device_stats.delay(device_id, start_time, end_time)
    return task.id

# Запуск анализа всех устройств пользователя
def start_user_analysis(db: Session, owner: str, start_time: datetime, end_time: datetime):
    task = analyze_user_devices.delay(owner, start_time, end_time)
    return task.id

# Получение результата анализа по ID задачи
def get_analysis_result(task_id: str):
    from .tasks import celery_app
    result = celery_app.AsyncResult(task_id)
    return result.get() if result.ready() else None