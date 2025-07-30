# Vehicle Environmental and Economic Impact Analysis
[![Python package](https://github.com/sweeteri/vehicle-analysis/actions/workflows/python-package.yml/badge.svg?branch=main)](https://github.com/sweeteri/vehicle-analysis/actions/workflows/python-package.yml)
## О проекте

Комплексный анализ экологического воздействия и экономической эффективности различных типов транспортных средств:

- Автомобили с ДВС (ICE)
- Электромобили (BEV)
- Подключаемые гибриды (PHEV)
- Гибриды (HEV)

**Цель**: Определить наиболее экологичные и экономичные транспортные решения для европейского региона.
## Ключевые метрики анализа
- Выбросы CO₂ (г/км)    
- Стоимость владения   
- Энергопотребление
### Технологии
- Python 3.12
- Django 5.2

### Запуск проекта в dev-режиме
```
# Клонирование репозитория
git clone https://github.com/sweeteri/vehicle-analysis.git
cd vehicle-analysis

# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Установка зависимостей
pip install -r requirements.txt
```
#### Настройка окружения
- В корневой папке проекта создайте файл .env
- Пропишите в этом файле следующие переменные:
```
SECRET_KEY=some_key
DEBUG=True
``` 
- В папке с файлом manage.py выполните одну из команд:
```
python3 manage.py runserver
```
```
python manage.py runserver
```
## Основные функции веб-интерфейса
1. Каталог автомобилей
- Фильтрация по типу ТС (ICE, BEV, PHEV, HEV)
- Детальные характеристики
- Сравнение моделей

2. Калькулятор эффективности
- Расчет выбросов CO₂
- Оценка стоимости владения
- Сравнение нескольких ТС

3. Симулятор эксплуатации
- Прогнозирование затрат
- Моделирование разных сценариев
- Визуализация временных рядов
