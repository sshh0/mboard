# mboard
Порядок запуска

Установить зависимости:
pip install django==4.1 django-precise-bbcode==1.2.15 django-simple-captcha==0.5.17 Pillow==9.2.0

В директории с файлом manage.py выполнить:  
python manage.py makemigrations mboard  
python manage.py migrate  
python manage.py shell  

Сгенерировать секретный ключ:  
from django.core.management.utils import get_random_secret_key; print(get_random_secret_key()) и вставить его в переменную SECRET_KEY в projectconfig/settings.py 

Затем создать две борды:  
from mboard.models import Board  
Board.objects.create(board_name='b')  
Board.objects.create(board_name='test')  

Выставить DEBUG = True в projectconfig/settings.py

Можно запускать: python manage.py runserver
