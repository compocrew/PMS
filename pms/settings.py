# Django settings for pms project.

import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG

import localsettings

#if DEBUG:
NO_COMPRESS_JS = True
NO_COMPRESS_CSS = True	


ADMINS = (
	('sivu', 'sivu@paeae.fi'),
)

INTERNAL_IPS = ('127.0.0.1',)


MANAGERS = ADMINS

DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.'+localsettings.DB, #postgresql_psycopg2', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
		'NAME': localsettings.DBNAME, #'pms',					   # Or path to database file if using sqlite3.
		'USER': localsettings.DBUSER, #'pms',						 # Not used with sqlite3.
		'PASSWORD': localsettings.DBPASSWORD, #'pms',					 # Not used with sqlite3.
		'HOST': localsettings.DBHOST,						 # Set to empty string for localhost. Not used with sqlite3.
		'PORT': localsettings.DBPORT,						 # Set to empty string for default. Not used with sqlite3.
	}
}

if hasattr(localsettings,"USE_MONGO") and localsettings.USE_MONGO:
	import mongoengine
	mongo = mongoengine.connect(localsettings.MONGOHOST)


PREPARE_UPLOAD_BACKEND = 'filetransfers.backends.default.prepare_upload'
SERVE_FILE_BACKEND = localsettings.DOWNLOAD_BACKEND
PUBLIC_DOWNLOAD_URL_BACKEND = 'filetransfers.backends.default.public_download_url'

ENTRY_UPLOAD_LOCATION = localsettings.UPLOAD_DIR

#for testing
EMAIL_BACKEND = localsettings.EMAIL_BACKEND
#for production
#EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST=localsettings.EMAIL_HOST

#EMAIL_BACKEND = "mailer.backend.DbBackend"

#CACHES = {
#	'default' : {
#		'BACKEND' : 'django.core.cache.backends.memcached.MemcachedCache',
#		'LOCATION' : 'memcached://127.0.0.1:11211/',
#		'TIMEOUT' : 60,
#	},
#}
CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True

SOUTH_DATABASE_ADAPTER = 'south.db.'+localsettings.DB


# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Helsinki'

TIME_FORMAT = "H:i"
# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(localsettings.ROOT,'media/')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/admin/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'km#yizhvzxx0s&2s_qf$+qoaasz8u=8is#&d==tdsykw@vwq-#=w%aw6v'

AUTH_PROFILE_MODULE = "accounts.UserProfile"

LOGIN_URL = "/accounts/login/"

PARTY_REDIRECT_EXCLUDE_URLS = (
	MEDIA_URL,
	'/admin',
	'/__debug__'
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
	'django.template.loaders.filesystem.Loader',
	'django.template.loaders.app_directories.Loader',
#	  'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
#	'django.middleware.cache.UpdateCacheMiddleware',
	'django.middleware.common.CommonMiddleware',
	'django.middleware.locale.LocaleMiddleware',
	'django.contrib.sessions.middleware.SessionMiddleware',
	'django.middleware.csrf.CsrfViewMiddleware',
	'django.contrib.auth.middleware.AuthenticationMiddleware',
	'django.contrib.messages.middleware.MessageMiddleware',
	'debug_toolbar.middleware.DebugToolbarMiddleware',
#	'django.middleware.cache.FetchFromCacheMiddleware',
)

DEBUG_TOOLBAR_PANELS = (
	'debug_toolbar.panels.timer.TimerDebugPanel',
	'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
	'debug_toolbar.panels.headers.HeaderDebugPanel',
#	'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
	'debug_toolbar.panels.template.TemplateDebugPanel',
	'debug_toolbar.panels.sql.SQLDebugPanel',
	'debug_toolbar.panels.signals.SignalDebugPanel',
	'debug_toolbar.panels.logger.LoggingPanel',
)

DEBUG_TOOLBAR_CONFIG = {
	'INTERCEPT_REDIRECTS' : False,
}

ROOT_URLCONF = 'pms.urls'

TEMPLATE_DIRS = (
	# Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
	# Always use forward slashes, even on Windows.
	# Don't forget to use absolute paths, not relative paths.
	os.path.join(localsettings.ROOT,'templates/'),
)

TEMPLATE_CONTEXT_PROCESSORS = (
	'main.context_processors.site_config',
	'main.context_processors.site_sections',
	"django.contrib.auth.context_processors.auth",
	"django.core.context_processors.debug",
	"django.core.context_processors.i18n",
	"django.core.context_processors.media",
	'django.core.context_processors.request',
	"django.contrib.messages.context_processors.messages",
	'django_messages.context_processors.inbox',
	'party.context_processors.party',
	'notification.context_processors.notification',
	'accounts.context_processors.user_info',
)

INSTALLED_APPS = (
	'django.contrib.auth',
	'django.contrib.contenttypes',
	'django.contrib.sessions',
	'django.contrib.sites',
	'django.contrib.messages',
#3rd party
	'south',
#	'mailer',
	'django_messages',
	'sorl.thumbnail',
	'piston',
	'debug_toolbar',

#own
	'api',
	'accounts',
	'party',
	'compo',
	'entry',
	'sports',
	'schedule',
	'news',
	'main',
#	'notifier',
#	'sms',
	'medialoader',
	'notification',
	#cms
	'django.contrib.sites',
	'django.contrib.markup',
	'django.contrib.humanize',
	
	# Uncomment the next line to enable the admin:
	'django.contrib.admin',

)
