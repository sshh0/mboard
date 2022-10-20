from pathlib import Path
from dotenv import dotenv_values

BASE_DIR = Path(__file__).resolve().parent.parent

dotenv_config = dotenv_values(".env")

SECRET_KEY = dotenv_config['SECRET_KEY']

DEBUG = True

ALLOWED_HOSTS = dotenv_config['ALLOWED_HOSTS'].split()

APPEND_SLASH = True

SESSION_COOKIE_AGE = 60 * 60 * 24 * 365 * 10  # ~ 10 years

CAPTCHA_FONT_SIZE = 27
CAPTCHA_LETTER_ROTATION = None
CAPTCHA_TEST_MODE = False
if Path.exists((BASE_DIR / 'captchawordsdict.txt')):
    CAPTCHA_WORDS_DICTIONARY = BASE_DIR / 'captchawordsdict.txt'
    CAPTCHA_CHALLENGE_FUNCT = 'captcha.helpers.word_challenge'
    CAPTCHA_FONT_PATH = 'fonts/DejaVuSans.ttf'
else:
    CAPTCHA_CHALLENGE_FUNCT = 'mboard.views.random_digit_challenge'

BBCODE_DISABLE_BUILTIN_TAGS = True
BBCODE_ALLOW_SMILIES = False
BBCODE_ESCAPE_HTML = []  # disable bbcode's esacaping
BBCODE_ALLOW_CUSTOM_TAGS = True
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'mboard.apps.MboardConfig',
    'captcha',
    'precise_bbcode',
    # 'debug_toolbar',
]

MIDDLEWARE = [
    # "debug_toolbar.middleware.DebugToolbarMiddleware",
    'django.middleware.http.ConditionalGetMiddleware',
    # 'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'projectconfig.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'projectconfig.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'en'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_TZ = True

LOCALE_PATHS = (
    BASE_DIR / 'locale',
)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = '/static/'

MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'

DATETIME_FORMAT = '%d/%m/%Y %H:%M'
# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
