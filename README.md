# vehicles-analysis

### Технологии
- Python 3.12
- Django 5.2

### Запуск проекта в dev-режиме
- Установите и активируйте виртуальное окружение
- Установите зависимости из файла requirements.txt
```
pip install -r requirements.txt
``` 
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