"""
Django settings for Elitelupus Staff Toolbox SAAS project.
"""

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-change-me-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Application definition
INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_spectacular',
    'corsheaders',
    'channels',
    'social_django',
    'django_celery_beat',
    
    # Local apps
    'apps.accounts',
    'apps.staff',
    'apps.counters',
    'apps.servers',
    'apps.templates_manager',
    'apps.rules',
    'apps.system_settings',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
    'apps.staff.middleware.StaffActivityMiddleware',  # Track staff activity
]

ROOT_URLCONF = 'config.urls'

# Disable automatic slash appending for REST API
APPEND_SLASH = False

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
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Channel Layers (Redis for WebSockets)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [(os.getenv('REDIS_HOST', 'redis'), int(os.getenv('REDIS_PORT', 6379)))],
        },
    },
}

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'elitelupus'),
        'USER': os.getenv('POSTGRES_USER', 'elitelupus'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'changeme'),
        'HOST': os.getenv('POSTGRES_HOST', 'db'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
    }
}

# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f"redis://{os.getenv('REDIS_HOST', 'redis')}:{os.getenv('REDIS_PORT', 6379)}/1",
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Password validation
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

# Authentication Backends
AUTHENTICATION_BACKENDS = (
    'apps.accounts.backends.SteamOpenId',  # Custom backend that reads API key from database
    'apps.accounts.backends.DiscordOAuth2',
    'apps.accounts.backends.StaffRosterAuthenticationBackend',  # Validates roster membership
    'django.contrib.auth.backends.ModelBackend',  # Fallback for local accounts
)

# Social Auth Settings
SOCIAL_AUTH_URL_NAMESPACE = 'social'

# Steam OAuth Settings (fallback if not in database)
SOCIAL_AUTH_STEAM_API_KEY = os.getenv('STEAM_API_KEY', '')
SOCIAL_AUTH_STEAM_EXTRA_DATA = ['player']

# Discord OAuth Settings
SOCIAL_AUTH_DISCORD_KEY = os.getenv('DISCORD_CLIENT_ID', '')
SOCIAL_AUTH_DISCORD_SECRET = os.getenv('DISCORD_CLIENT_SECRET', '')
SOCIAL_AUTH_DISCORD_SCOPE = ['identify']

# Discord Bot Settings (for staff status monitoring - OPTIONAL)
# Leave empty to disable Discord integration and use in-app activity tracking instead
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN', '')
DISCORD_GUILD_ID = os.getenv('DISCORD_GUILD_ID', '')  # Server ID to monitor

# Social Auth Pipeline
SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'apps.accounts.pipeline.create_or_link_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    'apps.accounts.pipeline.sync_staff_role',
)

# After OAuth completes, redirect to our callback view which generates JWT tokens
SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/api/auth/oauth/callback/'
SOCIAL_AUTH_NEW_USER_REDIRECT_URL = '/api/auth/oauth/callback/'
SOCIAL_AUTH_LOGIN_ERROR_URL = '/api/auth/oauth/error/'
LOGIN_REDIRECT_URL = '/api/auth/oauth/callback/'
LOGIN_ERROR_URL = '/api/auth/oauth/error/'

# Frontend URL for final redirect after JWT generation
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')

# REST Framework Settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# DRF Spectacular Settings (OpenAPI/Swagger)
SPECTACULAR_SETTINGS = {
    'TITLE': 'Elitelupus Staff Toolbox API',
    'DESCRIPTION': 'REST API for Elitelupus Staff Toolbox SAAS - Staff management, counters, server status, and more.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': r'/api/',
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': False,
    },
    'SECURITY': [
        {'Bearer': []},
    ],
    'TAGS': [
        {'name': 'Authentication', 'description': 'User authentication and registration'},
        {'name': 'Staff', 'description': 'Staff roster and management'},
        {'name': 'Counters', 'description': 'Sit/Ticket counter operations'},
        {'name': 'Servers', 'description': 'Game server status monitoring'},
        {'name': 'Templates', 'description': 'Refund templates and Steam lookup'},
        {'name': 'Rules', 'description': 'Server rules management'},
    ],
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# CORS Settings
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000').split(',')
CORS_ALLOW_CREDENTIALS = True

# CSRF Settings
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

# Add any additional origins from environment variable
if os.getenv('CSRF_TRUSTED_ORIGINS'):
    CSRF_TRUSTED_ORIGINS.extend(os.getenv('CSRF_TRUSTED_ORIGINS').split(','))

# For development, you might want to use a more lenient CSRF cookie setting
if DEBUG:
    CSRF_COOKIE_SAMESITE = 'Lax'
    CSRF_COOKIE_HTTPONLY = False
    SESSION_COOKIE_SAMESITE = 'Lax'
else:
    # Production settings
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SAMESITE = 'None'
    SESSION_COOKIE_SAMESITE = 'None'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Google Sheets Configuration
GOOGLE_SHEETS_ID = os.getenv('GOOGLE_SHEETS_ID', '1SSn3GXggr84dOYfQZzeHiRI0B1vaDkGynUyYHWfXIBo')
GOOGLE_SHEETS_CREDENTIALS_FILE = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE', 'credentials.json')

# Game Server Configuration
ELITE_SERVER_1 = (os.getenv('ELITE_SERVER_1_IP', '194.69.160.33'), int(os.getenv('ELITE_SERVER_1_PORT', 27083)))
ELITE_SERVER_2 = (os.getenv('ELITE_SERVER_2_IP', '193.243.190.12'), int(os.getenv('ELITE_SERVER_2_PORT', 27046)))

# Frontend URL
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')

# Celery Configuration
CELERY_BROKER_URL = f"redis://{os.getenv('REDIS_HOST', 'redis')}:{os.getenv('REDIS_PORT', 6379)}/0"
CELERY_RESULT_BACKEND = f"redis://{os.getenv('REDIS_HOST', 'redis')}:{os.getenv('REDIS_PORT', 6379)}/0"
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# Staff Role Priority Mapping
STAFF_ROLE_PRIORITIES = {
    'SYSADMIN': 0,
    'Manager': 10,
    'Staff Manager': 20,
    'Assistant Staff Manager': 30,
    'Assistant SM': 30,  # Abbreviated form
    'Meta Manager': 40,
    'Event Manager': 50,
    'Senior Admin': 60,
    'Snr Admin': 60,  # Abbreviated form
    'Admin': 70,
    'Senior Moderator': 80,
    'Snr Moderator': 80,  # Abbreviated form
    'Moderator': 90,
    'Senior Operator': 100,
    'Snr Operator': 100,  # Abbreviated form
    'Operator': 110,
    'T-Staff': 120,
}

# Role Colors for Frontend
STAFF_ROLE_COLORS = {
    'SYSADMIN': '#FF0000',
    'Manager': '#990000',
    'Staff Manager': '#F04000',
    'Assistant Staff Manager': '#8900F0',
    'Assistant SM': '#8900F0',  # Abbreviated form
    'Meta Manager': '#8900F0',
    'Event Manager': '#8900F0',
    'Senior Admin': '#d207d3',
    'Snr Admin': '#d207d3',  # Abbreviated form
    'Admin': '#FA1E8A',
    'Senior Moderator': '#15c000',
    'Snr Moderator': '#15c000',  # Abbreviated form
    'Moderator': '#4a86e8',
    'Senior Operator': '#38761d',
    'Snr Operator': '#38761d',  # Abbreviated form
    'Operator': '#93c47d',
    'T-Staff': '#b6d7a8',
}
