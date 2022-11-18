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
- Interface in English/Russian depending on browser language

#### Dependecies:
- Python 3.8+
- Django 4.1
- django-simple-captcha
- python-dotenv
- python-magic
- Pillow
- django-precise-bbcode
- FFmpeg

#### Installation:
```
pip install -r requirements.txt

python manage.py migrate

rename ".env.example" to ".env" in the root dir
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
- Post deletion password is specified in the "MOD_PASS" variable in .env file
