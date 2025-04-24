from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from . import crud, models, schemas, analitics
from .database import engine, SessionLocal
from datetime import datetime
import logging
from .tasks import celery_app
from .models import AnalysisResult

# Настройка логирования
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/devices/", response_model=schemas.Device)
def create_device(device: schemas.DeviceCreate, db: Session = Depends(get_db)):
    db_device = crud.create_device(db=db, device=device)
    return db_device

@app.post("/devices/{device_id}/stats/", response_model=schemas.StatResponse)
def create_stat(device_id: int, stat: schemas.StatCreate, db: Session = Depends(get_db)):
    return crud.create_stat(db=db, stat=stat, device_id=device_id)

@app.get("/devices/{device_id}/stats/", response_model=list[schemas.StatResponse])
def get_device_stats(device_id: int, start_time: datetime, end_time: datetime, db: Session = Depends(get_db)):
    return crud.get_stats_by_device(db=db, device_id=device_id, start_time=start_time, end_time=end_time)

@app.post("/devices/{device_id}/analyze/")
def analyze_device(device_id: int, request: schemas.AnalysisRequest, db: Session = Depends(get_db)):
    task_id = crud.start_device_analysis(db=db, device_id=device_id, 
                                       start_time=request.start_time, 
                                       end_time=request.end_time)
    return {"task_id": task_id}

@app.post("/users/{owner}/analyze/")
def analyze_user_devices(owner: str, request: schemas.AnalysisRequest, db: Session = Depends(get_db)):
    try:
        logger.info(f"Received analysis request for owner: {owner}")
        task_id = crud.start_user_analysis(db=db, owner=owner,
                                         start_time=request.start_time,
                                         end_time=request.end_time)
        if not task_id:
            raise HTTPException(status_code=404, detail=f"No devices found for owner {owner}")
        return {"task_id": task_id}
    except Exception as e:
        logger.error(f"Error processing analysis request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analysis/{task_id}/")
async def get_analysis_result(task_id: str, db: Session = Depends(get_db)):
    """Получение результата анализа по ID задачи"""
    try:
        # Сначала проверяем результат в базе данных
        result = db.query(AnalysisResult).filter(AnalysisResult.task_id == task_id).first()
        if result:
            return {
                "status": "success",
                "task_id": task_id,
                "result": {
                    "device_id": result.device_id,
                    "start_time": result.start_time,
                    "end_time": result.end_time,
                    "avg_x": result.avg_x,
                    "avg_y": result.avg_y,
                    "avg_z": result.avg_z,
                    "total_records": result.total_records
                }
            }
        
        # Если в базе нет, проверяем статус задачи в Celery
        task_result = celery_app.AsyncResult(task_id)
        
        if not task_result.ready():
            return {
                "status": "pending",
                "task_id": task_id
            }
            
        if task_result.failed():
            raise HTTPException(status_code=500, detail=str(task_result.result))
            
        result = task_result.get()
        if result is None:
            raise HTTPException(status_code=404, detail="Результат анализа не найден")
            
        # Если результат - словарь с task_id (результат analyze_user_devices)
        if isinstance(result, dict) and all(isinstance(v, str) for v in result.values()):
            # Получаем результаты для каждого устройства
            device_results = {}
            for device_id, device_task_id in result.items():
                device_result = db.query(AnalysisResult).filter(
                    AnalysisResult.task_id == device_task_id
                ).first()
                if device_result:
                    device_results[device_id] = {
                        "avg_x": device_result.avg_x,
                        "avg_y": device_result.avg_y,
                        "avg_z": device_result.avg_z,
                        "total_records": device_result.total_records
                    }
            
            return {
                "status": "success",
                "task_id": task_id,
                "results": device_results
            }
            
        # Если результат - одиночный анализ устройства
        return {
            "status": "success",
            "task_id": task_id,
            "result": result
        }
            
    except Exception as e:
        logger.error(f"Error getting analysis result: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/devices/{device_id}/analysis/")
async def get_device_analysis(device_id: int, db: Session = Depends(get_db)):
    """Получение всех результатов анализа для устройства"""
    try:
        # Получаем все результаты анализа для устройства
        results = db.query(AnalysisResult).filter(
            AnalysisResult.device_id == device_id
        ).all()
        
        if not results:
            raise HTTPException(status_code=404, detail="Результаты анализа не найдены")
        
        return {
            "status": "success",
            "device_id": device_id,
            "results": [
                {
                    "task_id": result.task_id,
                    "start_time": result.start_time.isoformat(),
                    "end_time": result.end_time.isoformat(),
                    "avg_x": result.avg_x,
                    "avg_y": result.avg_y,
                    "avg_z": result.avg_z,
                    "total_records": result.total_records
                }
                for result in results
            ]
        }
    except Exception as e:
        logger.error(f"Error getting device analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/devices/{device_id}/analytics/")
def get_device_analytics(
    device_id: int,
    start_time: datetime,
    end_time: datetime,
    db: Session = Depends(get_db)
):
    # Получение данных за указанный период
    stats = crud.get_stats_by_device(db, device_id, start_time, end_time)
    if not stats:
        raise HTTPException(status_code=404, detail="No stats found for the given period")

    # Извлечение значений x, y, z
    x_values = [stat.x for stat in stats]
    y_values = [stat.y for stat in stats]
    z_values = [stat.z for stat in stats]

    # Расчет статистики
    x_stats = analitics.calculate_statistics(x_values)
    y_stats = analitics.calculate_statistics(y_values)
    z_stats = analitics.calculate_statistics(z_values)

    return {
        "x": x_stats,
        "y": y_stats,
        "z": z_stats
    }