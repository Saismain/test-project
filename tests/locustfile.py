from locust import HttpUser, task, between
from datetime import datetime, timedelta
import random
import time

class DeviceUser(HttpUser):
    wait_time = between(1, 3)  # Время ожидания между запросами
    
    def on_start(self):
        """Выполняется при старте каждого пользователя"""
        # Создаем тестовое устройство
        self.device_id = f"test_device_{random.randint(1000, 9999)}"
        response = self.client.post("/devices/", json={
            "device_id": self.device_id,
            "owner": "test_user"
        })
        if response.status_code != 200:
            print(f"Failed to create device: {response.text}")
            return
            
        # Сохраняем числовой ID устройства из ответа
        self.numeric_device_id = response.json()["id"]
            
        # Добавляем начальную статистику для устройства
        for _ in range(5):  # Добавляем 5 записей статистики
            self.client.post(f"/devices/{self.numeric_device_id}/stats/", json={
                "x": random.uniform(-100, 100),
                "y": random.uniform(-100, 100),
                "z": random.uniform(-100, 100)
            })
        
        # Добавляем небольшую задержку, чтобы данные успели записаться
        time.sleep(1)

    @task(3)
    def add_stats(self):
        """Добавление статистики устройства"""
        self.client.post(f"/devices/{self.numeric_device_id}/stats/", json={
            "x": random.uniform(-100, 100),
            "y": random.uniform(-100, 100),
            "z": random.uniform(-100, 100)
        })

    @task(1)
    def get_stats(self):
        """Получение статистики устройства"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        self.client.get(
            f"/devices/{self.numeric_device_id}/stats/",
            params={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }
        )

    @task(1)
    def analyze_device(self):
        """Запуск анализа устройства"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        response = self.client.post(
            f"/devices/{self.numeric_device_id}/analyze/",
            json={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }
        )
        if response.status_code == 200:
            task_id = response.json()["task_id"]
            # Получаем результат анализа
            self.client.get(f"/analysis/{task_id}/") 