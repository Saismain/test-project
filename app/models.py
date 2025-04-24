from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class Device(Base):
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, unique=True, index=True)
    owner = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи с другими таблицами
    stats = relationship("Stat", back_populates="device")
    device_data = relationship("DeviceData", back_populates="device")
    analysis_results = relationship("AnalysisResult", back_populates="device")

class Stat(Base):
    __tablename__ = "stats"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    x = Column(Float)
    y = Column(Float)
    z = Column(Float)
    
    # Связь с устройством
    device = relationship("Device", back_populates="stats")

class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, unique=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    avg_x = Column(Float)
    avg_y = Column(Float)
    avg_z = Column(Float)
    total_records = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связь с устройством
    device = relationship("Device", back_populates="analysis_results")

class DeviceData(Base):
    __tablename__ = "device_data"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    x = Column(Float)
    y = Column(Float)
    z = Column(Float)
    
    # Связь с устройством
    device = relationship("Device", back_populates="device_data")