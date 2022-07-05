### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone "SSH код"
```

```
cd praktika
```

Cоздать и активировать виртуальное окружение:

```
python -m venv venv
```

```
source venv/Scripts/activate
```

Установить зависимости из файла requirements.txt:

```
python3 -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python manage.py migrate
```

Запустить проект:

```
cd yatube
```

```
python manage.py runserver 
```
