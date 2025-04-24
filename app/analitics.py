from statistics import median
from typing import List

def calculate_statistics(data: List[float]):
    """
    Вычисляет числовые характеристики для списка значений.
    :param data: Список чисел.
    :return: Словарь с результатами анализа.
    """
    if not data:
        return {
            "min": None,
            "max": None,
            "count": 0,
            "sum": 0,
            "median": None
        }
    return {
        "min": min(data),
        "max": max(data),
        "count": len(data),
        "sum": sum(data),
        "median": median(data)
    }