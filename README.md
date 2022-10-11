# mboard
Simple imageboard written in Python/Django

--------------------------------------------------------

#### Features:
- Javascript not required for basic functionality
- Image/webm upload/playback
- Reply previews
- Captcha 
- Ajax posting
- BB code tags
- Youtube embeds

#### Dependecies:
- django-simple-captcha  
- python-dotenv: for storing SECRET_KEY, ALLOWED_HOSTS without exposing them   
- python-magic: file uploading validation  
- Pillow: thumbnails creation
- django-precise-bbcode: BB code tags: [spoiler][/spoiler], [b][/b], [s][/s]...


#### Installation:
```
pip install -r requirements.txt

python manage.py migrate
```   


Run:  
```
python manage.py runserver
```
--------------------------------------------------------
### Notes:
- DEBUG mode is turned on. Turn it off if you're planning on deployng this imageboard:
DEBUG = False in projectconfig/settings.py
- Admin panel is available at /admin/ (run 'createsuperuser' command to create an admin user)  
- Uploading video files requires [FFmpeg](https://ffmpeg.org/) to be installed and present on the PATH variable.
