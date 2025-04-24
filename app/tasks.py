from celery import Celery
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from .database import SQLALCHEMY_DATABASE_URL
from .models import Device, Stat, AnalysisResult, DeviceData
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание экземпляра Celery
celery_app = Celery('tasks', broker='redis://redis:6379/0', backend='redis://redis:6379/0')

# Создание движка SQLAlchemy
engine = create_engine(SQLALCHEMY_DATABASE_URL)

@celery_app.task
def analyze_device_stats(device_id: int, start_time: datetime, end_time: datetime):
    """Анализ статистики устройства"""
    logger.info(f"Starting analysis for device {device_id}")
    
    try:
        with Session(engine) as db:
            # Получаем статистику устройства из таблицы stats
            stats = db.query(Stat).filter(
                Stat.device_id == device_id,
                #Stat.timestamp >= start_time,
                #Stat.timestamp <= end_time
            ).all()
            logger.info(f"Статистика собирается для {device_id}")
            
            if not stats:
                logger.warning(f"No stats found for device {device_id}")
                return None
                
            # Рассчитываем средние значения
            x_values = [stat.x for stat in stats]
            y_values = [stat.y for stat in stats]
            z_values = [stat.z for stat in stats]
            
            avg_x = sum(x_values) / len(x_values)
            avg_y = sum(y_values) / len(y_values)
            avg_z = sum(z_values) / len(z_values)
            
            # Создаем результат анализа
            result = AnalysisResult(
                task_id=analyze_device_stats.request.id,
                device_id=device_id,
                start_time=start_time,
                end_time=end_time,
                avg_x=avg_x,
                avg_y=avg_y,
                avg_z=avg_z,
                total_records=len(stats)
            )
            
            # Сохраняем результат в базу данных
            db.add(result)
            db.commit()
            
            return {
                "device_id": device_id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "avg_x": avg_x,
                "avg_y": avg_y,
                "avg_z": avg_z,
                "total_records": len(stats)
            }
            
    except Exception as e:
        logger.error(f"Error analyzing device stats: {str(e)}")
        raise

@celery_app.task
def analyze_user_devices(owner: str, start_time: datetime, end_time: datetime):
    """Анализ всех устройств пользователя"""
    logger.info(f"Starting analysis for owner: {owner}")
    
    with Session(engine) as db:
        # Получаем все устройства пользователя
        devices = db.query(Device).filter(Device.owner == owner).all()
        
        if not devices:
            logger.warning(f"No devices found for owner {owner}")
            return None
            
        results = {}
        for device in devices:
            logger.info(f"Starting analysis for device {device.device_id}")
            # Запускаем анализ для каждого устройства
            task = analyze_device_stats.delay(device.id, start_time, end_time)
            results[device.device_id] = task.id
            
        logger.info(f"Analysis tasks started for {len(devices)} devices")
        return results

@celery_app.task
def analyze_device_data(device_id: int, start_time: str, end_time: str):
    try:
        with Session(engine) as db:
            # Получаем данные устройства за указанный период
            device_data = db.query(Stat).filter(
                Stat.device_id == device_id,
                Stat.timestamp >= start_time,
                Stat.timestamp <= end_time
            ).all()
            
            if not device_data:
                logger.warning(f"No data found for device {device_id}")
                return None
            
            # Рассчитываем средние значения
            x_values = [data.x for data in device_data]
            y_values = [data.y for data in device_data]
            z_values = [data.z for data in device_data]
            
            avg_x = sum(x_values) / len(x_values)
            avg_y = sum(y_values) / len(y_values)
            avg_z = sum(z_values) / len(z_values)
            
            # Создаем запись с результатами анализа
            analysis_result = AnalysisResult(
                task_id=analyze_device_data.request.id,
                device_id=device_id,
                start_time=start_time,
                end_time=end_time,
                avg_x=avg_x,
                avg_y=avg_y,
                avg_z=avg_z,
                total_records=len(device_data)
            )
            
            db.add(analysis_result)
            db.commit()
            
            logger.info(f"Analysis completed for device {device_id}")
            return analysis_result
            
    except Exception as e:
        logger.error(f"Error analyzing device {device_id}: {str(e)}")
        return None

@celery_app.task
def analyze_all_devices(start_time: str, end_time: str):
    try:
        with Session(engine) as db:
            # Получаем все устройства
            devices = db.query(Device).all()
            
            if not devices:
                return {
                    "status": "error",
                    "message": "Нет доступных устройств"
                }
            
            # Создаем задачи для каждого устройства
            results = []
            for device in devices:
                task = analyze_device_data.delay(
                    device_id=device.id,
                    start_time=start_time,
                    end_time=end_time
                )
                results.append({
                    "device_id": device.id,
                    "task_id": task.id
                })
            
            logger.info(f"Analysis tasks started for {len(devices)} devices")
            return results
            
    except Exception as e:
        logger.error(f"Error starting analysis tasks: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }
