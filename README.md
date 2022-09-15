# mboard
Простая имиджборда, сделанная в стиле 2ch/4chan

#### Установка:
```
pip install -r requirements.txt
```   
В директории с файлом manage.py последовательно выполнить:  
```
python manage.py makemigrations mboard  
python manage.py migrate  
python manage.py shell  
from mboard.models import Board  
Board.objects.create(board_name='b')  
Board.objects.create(board_name='test')  
exit()
```
Запустить:  
```
python manage.py runserver
```
--------------------------------------------------------
Для основной работоспособности необязательно, но для загрузки webm/mp4 файлов требуется [FFmpeg](https://ffmpeg.org/), доступный через PATH переменную.  

