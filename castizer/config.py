import inspect
import logging
import os
import platform


DEBUG = True
DEBUG_LAUNCH_FROM_LIGHTTPD = False

ACTION_ERROR = 0
ACTION_JUST_BOOTED = 1
ACTION_SWITCH_ON = 2
ACTION_SWITCH_OFF = 3
ACTION_VOLUME = 4
ACTION_CHANNEL = 5
ACTION_JOY_X = 6
ACTION_JOY_Y = 7
ACTION_JOY_BUTTON = 8

ENABLE_BUTTONS = 0
ENABLE_SENSORS = 1

LIMITED_PLAYLIST_CONTROL_BASED_ON_FOLDERS = True
MUSIC_FOLDERS = ['1', '2', '3', '4']
#MUSIC_FOLDERS = ['1', '2', '3', '4', '5', '6']

logging.basicConfig(level=logging.DEBUG if DEBUG else logging.WARNING)

THIS_DIR = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
HOME = os.path.realpath(os.path.join(THIS_DIR, '..'))

DATABASES_PATH = os.path.join(HOME, 'databases')
AUDIOFILES_PATH = os.path.join(HOME, 'audiofiles')
PLUGINS_PATH = os.path.join(HOME, 'src/plugins')

SRC_PATH = os.path.join(HOME, 'src')

logging.basicConfig(level=logging.DEBUG if DEBUG else logging.WARNING, filename=os.path.join(HOME, 'logs/logging.log'))

UPDATE_SERVERNAME = "www.aquaolympic.com/www/ctz/updates"
#UPDATE_SERVERNAME = "www.castizer.com/updates"
#UPDATE_SERVERNAME = "pc-pablo.dacya.ucm.es"

#UPDATE_FLAG = "/root/config/update"
#UPDATE_FOLDER = "/root/update"
# Should it go into the ./config/update folder?

UPDATES_PATH = os.path.join(HOME, 'update')
UPDATE_FLAG = os.path.join(UPDATES_PATH, 'update')
UPDATE_PACKAGE_PATH = os.path.join(UPDATES_PATH, 'update_package')

HOST_NAME = platform.node()

current_song_URL = "ERROR"
current_song_file = "filenameEMPTY"
current_song_path = "pathnameEMPTY"
sendTo = "ERROR"

received_song_url =  "NoSongReceived"
                                
JSON_OUTFILE = "json_incoming_songs.txt"
C_SAMBA_SERVER_LOCAL = 'localhost'
C_RECEIVED_FOLDER = 'received'    
            
C_FRIENDS_ALBERTO = 'alberto'
C_FRIENDS_ANNA = 'anna'
C_FRIENDS_COQUI = 'coqui'
C_FRIENDS_PABLO = 'pablo'

if HOST_NAME in ('OpenWrt', 'dubber', 'castizer'):
    print 'PLATFORM=CASTIZER'
    PLATFORM = 'castizer'
    VOLUME_INIT = 2
    # LOGITECH INFO
    BUTTONS_EVDEV_FILE = '/dev/input/event0'
    BUTTON_VOL_UP = 115 # VOL_UP_KEY
    BUTTON_ACTION = 114 # VOL_DOWN_KEY
    BUTTON_VOL_DOWN = 113 # MUTE_KEY
elif HOST_NAME in ('cloudcaster'):
    PLATFORM = 'pc'
    print 'PLATFORM=pc'
    VOLUME_INIT = 50
    BUTTONS_EVDEV_FILE = '/dev/input/event0'
    SENSORS_SERIAL_PORT = '/dev/pts/2'
    BUTTON_PREV = 30      # a
    BUTTON_NEXT = 32      # d
    BUTTON_RECEIVE = 16   # q
    BUTTON_VOL_UP = 17    # w
    #BUTTON_SEND_ANNA = 18      # e 
    #BUTTON_SEND_ALBERTO = 19      # r
    BUTTON_SEND_PABLO = 18      # e
    BUTTON_SEND_COQUI = 19      # r
    BUTTON_ACTION = 31      # s
    BUTTON_STOP = 44    # z
    BUTTON_VOL_DOWN = 45    # x
    BUTTON_GET_INCOMING_SONG = 46 # c
    BUTTON_DEBUG = 47 # v
    BUTTON_UPDATEDB = 22 # u
    BUTTON_QUIT = 16 # q
    HOME_PATH = "/home/d/cloudcaster"
    C_OWNER = 'pablo'
    sendFrom = "coqui"
elif HOST_NAME in ('cccoqui'):
    PLATFORM = 'RASPI'
    print 'PLATFORM=', PLATFORM
    VOLUME_INIT = 10
    # when plugged in the USB sound card, it becomes event1. event0 otherwise
    BUTTONS_EVDEV_FILE = '/dev/input/event1'
    BUTTON_PREV = 30      # a
    BUTTON_NEXT = 32      # d
    BUTTON_RECEIVE = 16   # q
    BUTTON_VOL_UP = 17    # w
    #BUTTON_SEND_ANNA = 18      # e 
    #BUTTON_SEND_ALBERTO = 19      # r 
    BUTTON_SEND_COQUI = 18      # e
    BUTTON_SEND_PABLO = 19      # r
    BUTTON_ACTION = 31      # s
    BUTTON_STOP = 44    # z
    BUTTON_VOL_DOWN = 45    # x
    BUTTON_GET_INCOMING_SONG = 46 # c
    BUTTON_DEBUG = 47 # c
    BUTTON_UPDATEDB = 22
    BUTTON_QUIT = 16 # q
    HOME_PATH = "/home/pi/cloudcaster"
    C_OWNER = 'coqui'
    sendFrom = "pablo"
#elif HOST_NAME in ('ubuntu'):
#    PLATFORM = 'pc'
#    print 'PLATFORM=pc'
#    BUTTONS_EVDEV_FILE = '/dev/input/event1'
elif HOST_NAME in ('devmachine'):
    PLATFORM = 'devmachine'
    print 'PLATFORM=devmachine'
    BUTTONS_EVDEV_FILE = '/dev/input/event0'
    BUTTON_ACTION = 41 # Tecla a la izquierda del 1
    BUTTON_VOL_DOWN = 2 # 1
    BUTTON_VOL_UP = 3 # 2
    BUTTON_DEBUG = 4 # 3
    BUTTON_QUIT = 16 # q
    VOLUME_INIT = 50
else:
    PLATFORM = 'unknown'
    print 'PLATFORM=unknown'
    BUTTONS_EVDEV_FILE = '/dev/input/event0'
    VOLUME_INIT = 100
    BUTTON_ACTION = 115
    BUTTON_VOL_UP = 114
    BUTTON_VOL_DOWN = 113

FILES_PATH = HOME_PATH + "/cc_files"
MUSIC_PATH = FILES_PATH + "/music"
C_SHARES_FOLDER = FILES_PATH + "/shares"

#BUTTON_ACTION = 113
#BUTTON_VOL_UP = 114
#BUTTON_VOL_DOWN = 115
#BUTTON_HOLDS_LONG_CLICK = 5
BUTTON_HOLDS_VERY_LONG_CLICK = 15
BUTTON_HOLDS_EXTRA_LONG_CLICK = 50

BUTTONS_POLL_TIMEOUT = 0.3

READ_BYTES = 512

WEB_SERVER_PORT = 8080

LED_NAME = 'tp-link:blue:system'

GOLDEN_CONFIGURATION_NETWORK_FILES = "../golden_configuration/network/*"

if DEBUG == 'False':
    SOUND_START = 'resources/dreamcast.wav'
else:
    SOUND_START = 'resources/sonar.wav'
SOUND_SLEEP = 'resources/sleep.wav'
SOUND_WAKEUP = 'resources/wakeup.wav'
SOUND_EXTRAFEATURE = 'resources/encendido_completado.wav'

SOUND_RESET_NETWORK = 'resources/reset_network.wav'
SOUND_RESET_NETWORK_ERROR = 'resources/reset_network_error.wav'
#SOUND_RESET_NETWORK_ERROR = 'resources/alarm.wav'
SOUND_RESET_NETWORK_COMPLETED = 'resources/reset_network_completed.wav'
#SOUND_RESET_NETWORK_COMPLETED = 'resources/sonar.wav'

SOUND_UPDATE = 'resources/update.wav'
SOUND_UPDATE_UPTODATE = 'resources/update_uptodate.wav'
SOUND_UPDATE_ERROR_OTHER = 'resources/update_network_error_other.wav'
SOUND_UPDATE_ERROR_INTERNET = 'resources/update_network_error_internet.wav'
SOUND_UPDATE_COMPLETED = 'resources/update_completed.wav'

SOUND_UPDATE_MUSIC_DB = 'resources/update_music_db.wav'
SOUND_UPDATE_MUSIC_DB_COMPLETED = 'resources/update_music_db_completed.wav'

SOUND_WARNING_ALARM = 'resources/sonar.wav'

SOUND_SENDING_SONG_TO = 'resources/sending_song_to.mp3'
SOUND_ALBERTO = 'resources/alberto.mp3'
SOUND_ANNA = 'resources/anna.mp3'
SOUND_COQUI = 'resources/anna.mp3'
SOUND_PABLO = 'resources/alberto.mp3'


SOUND_SEND_OK = 'resources/sonar.wav'

