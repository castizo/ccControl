from os import mkdir, geteuid, chdir
from os.path import join, dirname, abspath
from subprocess import call
from sys import exit
#import src
#import src.config
#import src.main
from castizer import config, main
import time
#import pickle 

# if src.config.PLATFORM == 'castizer':    
#     base_path = abspath(dirname(__file__))
#     base_path = '/root/castizer-control/'
# elif src.config.PLATFORM == 'devmachine':
#     base_path = abspath(dirname(__file__))
# else:
#     print 'Run configuration: PLATFORM=other'

base_path = abspath(dirname(__file__))

#MUSIC_DIR = join(base_path, 'audiofiles')
PLAYLISTS_DIR = join(base_path, 'mpd/playlists')
DATABASE_FILE = join(base_path, 'mpd/tag_cache')
LOG_FILE = join(base_path, 'logs/mpd.log')
PID_FILE = join(base_path, 'mpd/pid')
STATE_FILE = join(base_path, 'mpd/state')
STICKER_FILE = join(base_path, 'mpd/sticker.sql')    

#MUSIC_DIR = '/home/d/cloudcaster/cc_samba/music'
PLAYLISTS_DIR = config.FILES_PATH + '/playlists'
DATABASE_FILE = config.FILES_PATH + '/mpd/tag_cache'
LOG_FILE = config.FILES_PATH + '/mpd/mpd.log'
PID_FILE = config.FILES_PATH + '/mpd/pid'
STATE_FILE = config.FILES_PATH + '/mpd/state'
STICKER_FILE = config.FILES_PATH + '/mpd/sticker.sql'    

MPD_CONF_CASTIZER = '''
    bind_to_address "localhost"
    port "6600"
    #user "mpd"
    auto_update "yes"
    audio_output {
        type "alsa"
        name "My ALSA Device"
        device "hw:0,0"
        format "44100:16:2"
        mixer_device "default"
        mixer_control "PCM"
        mixer_index "0"
    }
    audio_output_format            "44100:16:1"
'''

# MPD_CONF_HEAD = """
#     music_directory        "{MUSIC_DIR}"
#     playlist_directory     "{PLAYLISTS_DIR}"
#     db_file                "{DATABASE_FILE}"
#     log_file               "{LOG_FILE}"
#     pid_file               "{PID_FILE}"
#     state_file             "{STATE_FILE}"
#     sticker_file           "{STICKER_FILE}"    
# """

MPD_CONF_HEAD = """
    music_directory        "{config.MUSIC_PATH}"
    playlist_directory     "{PLAYLISTS_DIR}"
    db_file                "{DATABASE_FILE}"
    log_file               "{LOG_FILE}"
    pid_file               "{PID_FILE}"
    state_file             "{STATE_FILE}"
    sticker_file           "{STICKER_FILE}"    
"""

#user                    "d"    
MPD_CONF_REST = """
    bind_to_address         "localhost"
    port                    "6600"
    auto_update             "yes"
    audio_output {
            type            "alsa"
            name            "My ALSA Device"
            device          "hw:0,0"    # optional
            format          "44100:16:2"    # optional
            mixer_device    "default"       # optional
            mixer_control   "PCM"           # optional
            mixer_index     "0"             # optional
            mixer_type      "software"      # optional            
    }
"""
    
MPD_CONF_REST_RASPI = """
    bind_to_address         "localhost"
    port                    "6600"
    auto_update             "yes"
    audio_output {
            type            "alsa"
            name            "My ALSA Device"
            device          "hw:1,0"    # optional
            format          "44100:16:2"    # optional
            mixer_device    "default"       # optional
            mixer_control   "PCM"           # optional
            mixer_index     "0"             # optional
            mixer_type      "software"      # optional            
    }
"""

MPD_CONF_PATH = '/tmp/mpd.conf'
file_handler = open(MPD_CONF_PATH, "w")

#if not geteuid():
#    print 'You must run this script as root'
#    exit(1)

for d in ['audiofiles', 'databases', 'logs', config.MUSIC_PATH, PLAYLISTS_DIR]:
    try:
        mkdir(d)
    except:
        pass

if config.PLATFORM == 'castizer':    
    print 'Run configuration: PLATFORM=CASTIZER'
    #file_handler.write(expandvars(MPD_CONF_CASTIZER)) 
    file_handler.write(MPD_CONF_HEAD.format(**locals()))
    file_handler.write(MPD_CONF_CASTIZER)
    print "Killing old instances of mpd..."
    call(['killall', 'mpd'])
    # let some time to close the port so that it can be reopened
    time.sleep(1)
    chdir(config.MUSIC_PATH)
elif config.PLATFORM == 'RASPI':
    print 'CHECKPOINT'
    print 'Run configuration: PLATFORM=', config.PLATFORM
    #file_handler.write(expandvars(MPD_CONF))
    #locals()
    file_handler.write(MPD_CONF_HEAD.format(**locals()))
    file_handler.write(MPD_CONF_REST_RASPI)
    print "Killing old instances of mpd..."
    call(['killall', 'mpd'])
    # let some time to close the port so that it can be reopened
    time.sleep(1)
elif config.PLATFORM == 'devmachine' or 'pc':
    print 'Run configuration: PLATFORM=', config.PLATFORM
    #file_handler.write(expandvars(MPD_CONF))
    #locals()
    file_handler.write(MPD_CONF_HEAD.format(**locals()))
    file_handler.write(MPD_CONF_REST)
    print "Killing old instances of mpd..."
    call(['killall', 'mpd'])
    # let some time to close the port so that it can be reopened
    time.sleep(1)
else:
    print 'Run configuration: PLATFORM=other'
        
print "Finished."
file_handler.close()

print ">>> Checkpoing before launching MPD"
call(['mpd', MPD_CONF_PATH])
print ">>> Checkpoing after launching MPD"

#if src.config.PLATFORM != 'castizer':
#    src.main.main()

main.main()

