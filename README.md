# mboard
Simple imageboard written in Python/Django

--------------------------------------------------------

#### Features:
- Javascript not required for basic functionality
- Image/webm upload/playback
- Reply previews
- Captcha 
- Ajax posting
- BB code tags: [spoiler][/spoiler], [b][/b], [s][/s]...
- Youtube embeds

#### Dependecies:
- django-simple-captcha: captcha  
- python-dotenv: for storing SECRET_KEY, ALLOWED_HOSTS without exposing them   
- python-magic: file uploading validation  
- Pillow: thumbnails creation


#### Installation:
```
pip install -r requirements.txt
```   


Run:  
```
python manage.py runserver
```
--------------------------------------------------------
### Notes:
- Admin panel is available at /admin/ (login: 'test', password: 'test')  
- Uploading video files requires [FFmpeg](https://ffmpeg.org/) to be installed and present on the PATH variable.
