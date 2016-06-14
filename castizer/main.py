import buttons
import config
import updater
import plugins
import mpd
import threading
import Queue
import logging
import random
import bottle
import time
#TODO: Only is used for os->reboot to install updates... look for alternative way to do it
import os
from flup.server.fcgi import WSGIServer
#import subprocess

if config.PLATFORM == 'castizer':
    import leds
else:
    import dummyleds as leds


LOG = logging.getLogger('Main Controller')


class Controller(threading.Thread):

    def __init__(self):
        super(Controller, self).__init__()
        self.daemon = True
        self.exit_event = threading.Event()
        #self.plugins = plugins.load_all()
        self.buttons = buttons.ButtonReader(config.BUTTONS_EVDEV_FILE)
        self.buttons.register(self.buttons_callback)
        self.buttons.start()
        self.queue = Queue.Queue()
        self.folder_index = -1
        self.folders = config.MUSIC_FOLDERS
        self.mpd = mpd.MPDClient()
        self.mpd.connect('127.0.0.1', 6600)
        self.led = leds.LED(config.LED_NAME)
        self.updater = updater.Updater()
        self.justBooted()
        self.saved_song = 0
        self.saved_time = 0

    def buttons_callback(self, keycode, clicks, holds):
        # Beware: this code will run in the buttons thread
        #if config.DEBUG:
        print 'KEY CODE:', keycode, 'CLICKS:', clicks, 'HOLDS:', holds
        self.queue.put_nowait((keycode, clicks, holds))

    def run(self):
        while not self.exit_event.is_set():
            try:
                keycode, clicks, holds = self.queue.get(block=True, timeout=1)
            except Queue.Empty:
                continue
            self.button_event(keycode, clicks, holds)

    def playStartSound(self):
        self.playSound(config.SOUND_START)
        
    def playSound(self, sound_url):
        l = logging.getLogger('controller.event')
        l.debug('Playing sound...')
        #play wake_up sound
        self.mpd.clear()
        self.mpd.repeat(0)
        print sound_url
        self.mpd.add(sound_url)
        self.mpd.play()
        #self.mpd.send_idle()
        #event = self.mpd.fetch_idle()
        playing = 'play'
        while  playing == 'play':
            status = self.mpd.status()
            playing = status['state']
            time.sleep(0.2)
        #self.mpd.repeat(1)       
        self.mpd.clear()

    def justBooted(self):
        self.mpd.setvol(config.VOLUME_INIT)
        self.playStartSound()
        l = logging.getLogger('controller.event')
        l.debug('LED on')        
        self.led.on()
        self.sleeping = 0
        
    def load_random_playlist(self):
        playlists = [p['playlist'] for p in self.mpd.listplaylists()]
        #cur = #TODO: get name of current playlist
        #idx = playlists.index(cur)
        #nxt = playlists[idx % len(playlists)]
        if not playlists:            
            print 'Empty playlist folder !!!'
        else:
            nxt = random.choice(playlists)
            print 'NEXT:', nxt
            self.mpd.clear()
            self.mpd.load(nxt)
            self.mpd.play()

    def toggle(self):
        l = logging.getLogger('controller.event')
        status = self.mpd.status()
        #print status
        if status['state'] == 'play':
            l.debug('state is PLAYING, Next song.')
            self.mpd.next()
        elif int(status['playlistlength']) > 0: # Playlist not empty
            self.mpd.play()
        else:
            l.debug('empty playlist, loading one')
            #idx = self.dirs[self.dir_index % len(self.dirs)]
            #dir = str(idx)
            #self.loadItem(dir) 
            self.change_playlist()
    
    def load_next_folder(self):
        self.folder_index = (self.folder_index+1) % len(self.folders)
        folder_to_play = self.folders[self.folder_index]
        print 'NEXT playlist (FOLDER MODE):', folder_to_play        
        self.mpd.clear()
        try:
            self.mpd.add(folder_to_play)
        except mpd.CommandError: 
            print 'Error loading playlist (FOLDER MODE) !'        
        self.mpd.play()

    def change_playlist(self):
        if config.LIMITED_PLAYLIST_CONTROL_BASED_ON_FOLDERS:
            self.load_next_folder()
            self.mpd.random(1)
        else:
            self.load_random_playlist()

    def shut_down(self):
        # Some kind of processor sleep command would be better, but we're lean <- Man, I love your comments!
        l = logging.getLogger('controller.event')
        l.debug('shutting down...')
        self.sleep()
        
    def sleep(self):
        l = logging.getLogger('controller.event')
        l.debug('sleep...')
        self.saveSoundContext()
        self.playSound(config.SOUND_SLEEP)
        self.sleeping = 1
        l.debug('LED off')        
        self.led.off()
        #self.mpd.pause()

    def wakeup(self):
        self.sleeping = 0
        l = logging.getLogger('controller.event')
        l.debug('LED on')
        self.led.on()
        self.restoreSoundContext()

    def extraFeature(self):
        self.saveSoundContext()
        self.playSound(config.SOUND_EXTRAFEATURE)
        self.restoreSoundContext()

    def warn(self):
        self.mpd.clear()
        self.mpd.stop()
        self.mpd.setvol(config.VOLUME_INIT)       
        self.sleeping = 1
        self.led.on() 
        self.playSound(config.SOUND_WARNING_ALARM)
        
    def resetNetwork(self):
        l = logging.getLogger('controller.event')
        l.debug('resetNetwork(): BEGIN')
        self.led.on() 
        self.playSound(config.SOUND_RESET_NETWORK)
        l.debug('Restoring network files...')
        command = "cp " + config.GOLDEN_CONFIGURATION_NETWORK_FILES + " /etc/config/"        
        try: 
            wget_status = os.system(command)
        except: 
            l.debug('resetNetwork(): ERROR during file copy')
            l.debug('DEBUG INFO: ' + sys.exc_info()[1])
            self.playSound(config.SOUND_RESET_NETWORK_ERROR)
            return -1
        if wget_status == 0:
            l.debug('Network files restored succesfully !')
            self.playSound(config.SOUND_RESET_NETWORK_COMPLETED)
            l.debug('resetNetwork(): END')
            l.debug('rebooting...')
            os.system("reboot")                    
        else:
            l.debug('resetNetwork(): ERROR during file copy')
            self.playSound(config.SOUND_RESET_NETWORK_ERROR)
            return -1
        
    def hasInternetConnection(self):
        l = logging.getLogger('controller.event')
        l.debug('Testing if Castizer can access the internet')
        #command = "wget -q --tries=10 --timeout=20 http://google.com"        
        command = "wget -q -s http://google.com"
        try: 
            ping_status = os.system(command)
        except: 
            print 'ERROR: hasInternetConnection'
        if ping_status == 0:
            l.debug('Successfully reached google.com')
            return 1
        else:
            l.debug('Did not get reply from google.com')
            return 0
        
    def update(self):
        l = logging.getLogger('controller.event')
        l.debug('Launching update process...')                    
        l.debug('>>> Playing update recording')
        self.playSound(config.SOUND_UPDATE)
        #updater.getCurrentVersion()
        #updater.printNewestVersion()
        exit_code = self.updater.update()

        print "updater.update() exited with code <" + str(exit_code) + ">" 
        self.playSound(config.SOUND_WARNING_ALARM)

        if self.hasInternetConnection():
            
            if exit_code == 0:
                l.debug('No updates were detected. CastizerS soul is up to date. Relax and Enjoy.')
                self.playSound(config.SOUND_UPDATE_UPTODATE)
            elif exit_code < 0:
                l.debug('An error occurred during the update process.')
                l.debug('Please, try again later.')
                l.debug('May the problem persist, please, contact your distributor.')
                l.debug('>>> ERROR UPDATING !')                    
                self.playSound(config.SOUND_UPDATE_ERROR_OTHER)
            else:
                l.debug('An update has been succesfully downloaded')
                l.debug('Proceeding to installation: Castizer will now reboot.')                    
                l.debug('>>> REBOOTING...')                    
                self.playSound(config.SOUND_UPDATE_COMPLETED)
                os.system("reboot")
                l.debug('UPDATE PROCESS COMPLETED !')
        else:
            l.debug('No internet connection available. Please, set up a valid internet connection before updating.')                                
            self.playSound(config.SOUND_UPDATE_ERROR_INTERNET)

    def restoreSoundContext(self):
        print('restoring context...')
        self.mpd.clear()
        try:
            self.mpd.load('pl_current')
        except mpd.CommandError: 
            print 'There was no pl_current playlist'
            self.change_playlist()
            return
        if self.saved_song > -1:
            self.mpd.seek(self.saved_song, self.saved_time)
        self.mpd.play()

    def saveSoundContext(self):
        self.mpd.pause()
        try:
            self.mpd.rm('pl_current')
        except mpd.CommandError: 
            print 'There was no pl_current playlist'        
        self.mpd.save('pl_current')
        status = self.mpd.status()
        #print status
        if 'song' in status:
            print ('Song is ', status['song'])
            self.saved_song = status['song']
            if 'elapsed' in status:
                time = status['elapsed']
                time = time.split('.')
                elapsed_secs = time[0]
            else:
                # An error occurred. TODO: track it !
                elapsed_secs = 0
            self.saved_time = elapsed_secs   
        else:
            print 'No song'
            self.saved_song = -1
            self.saved_time = -1   
        print 'SAVED CONTEXT *************************'                        
        #print self.saved_time                        
        #print self.saved_song
        #print(status)
        #print 'SAVED CONTEXT *************************'                        
        
    def getCurrentSongURL(self):
        l = logging.getLogger('controller.event')
        l.debug('getSoundContext() BEGIN')        
        status = self.mpd.status()
        #print status
        if 'song' in status:
            self.current_song_info = self.mpd.currentsong()
            if 'file' in self.current_song_info:
                self.current_song_URL = self.current_song_info['file']
                print ('getCurrentSongURL: Song URL: ', self.current_song_URL)
            else:
                # An error occurred. TODO: track it !
                print ('ERROR: getSoundContext', )
        else:
            print 'No song'
            self.song_to_send = "ERROR"
        l.debug('getSoundContext() END')                

    def sendSong(self, person):
        l = logging.getLogger('controller.event')
        self.getCurrentSongURL()
        print ('Song URL: ', self.current_song_URL)
        self.saveSoundContext()
        self.playSound(config.SOUND_SENDING_SONG_TO)
        if (person == config.BUTTON_SEND_ANNA):
            self.playSound(config.SOUND_ANNA)
        elif (person == config.BUTTON_SEND_ALBERTO):
            self.playSound(config.SOUND_ALBERTO)
        else:
            l.debug('ERROR: main.sendSong')                    
            self.playSound(config.SOUND_WARNING_ALARM)

        fullpath = self.current_song_URL
        path, file = os.path.split(fullpath)
        l.debug('path: ' + path)
        l.debug('file: ' + file)
        
        command = "smbclient //localhost/cc_samba -c 'md \"" + path + "\";  put \"" + config.MUSIC_PATH + "/" + self.current_song_URL + "\" \"" + self.current_song_URL + "\"' -U usersamba pass"
        print 'COMMAND: ', command
        
        try: 
            command_status = os.system(command)
        except: 
            l.debug('sendSong(): ERROR during file copy')
            return -1
        if command_status == 0:
            l.debug('sendSong() file sent succesfully !')
            self.playSound(config.SOUND_SEND_OK)
            #self.playSound(config.SOUND_RESET_NETWORK_COMPLETED)
            #l.debug('resetNetwork(): END')
        else:
            l.debug('sendSong(): ERROR during file copy')
            self.playSound(config.SOUND_WARNING_ALARM)
            return -1

        self.restoreSoundContext()

    def nullifySoundContext(self):
        l = logging.getLogger('controller.event')
        l.debug('nullifySoundContext...')                    
        self.mpd.stop()
        self.mpd.clear()
        self.saveSoundContext()
        try:
            self.mpd.rm('pl_current')
        except mpd.CommandError: 
            l.debug('nullifySoundContext: There was no pl_current playlist')        

    def volume(self, amount):
        l = logging.getLogger('controller.event')
        stat = self.mpd.status()
        vol = int(stat['volume'])
        if (amount > 0) and (vol > 100):
            l.debug('Volume Up event received with volume above the limit. Nothing is done.')
        else:
            try:
                self.mpd.setvol(vol + amount)
            except mpd.CommandError: 
                l.debug('Volume out of bounds ! (under/over-flow)')

    def debug(self, clicks):
        if clicks == 1:
            estado = self.mpd.status()
            print(estado)
            print('state: <', estado['state'], '>')
            #print(self.mpd.shuffle())
            #sprint ("Call to random: <", self.mpd.random(1), ">")
        elif clicks == 2:
            print("> Stop")
            self.mpd.stop()
        elif clicks == 3:
            print('restoring context...')
            self.mpd.clear()
            self.mpd.load('pl_current')
            #self.mpc.load('pol')
            #self.mpc.seek(1, 10)      
            self.mpd.seek(self.saved_song, self.saved_time)
            self.mpd.play()
            
    def isLongClick(self, clicks, holds):
        if holds == 1:
            return True
        return False
    
    def isVeryLongClick(self, clicks, holds):
        if holds == config.BUTTON_HOLDS_VERY_LONG_CLICK:
            return True
        return False

    def isExtraLongClick(self, clicks, holds):
        if holds == config.BUTTON_HOLDS_EXTRA_LONG_CLICK:
            return True
        return False

    def button_event(self, keycode, clicks, holds):
        l = logging.getLogger('controller.event')
        if keycode == config.BUTTON_UPDATEDB:
                l.debug('action, BUTTON_UPDATEDB')
                l.debug('>>> Updating MUSIC DataBase')                    
                self.warn()
                self.nullifySoundContext()
                self.playSound(config.SOUND_UPDATE_MUSIC_DB)
                time.sleep(1)
                #print self.mpd.status()
                self.mpd.update()
                #print self.mpd.status()
                updating = 1
                while updating != 0:
                    status = self.mpd.status()
                    if 'updating_db' in status:
                        updating = status['updating_db']
                        l.debug('>>> updating_db = ' + str(updating))
                        time.sleep(0.1)
                    else:
                        updating = 0                        
                        l.debug('>>> updating_db = <> ')
                l.debug('>>> Updating MUSIC DataBase COMPLETED')                    
                self.warn()
                self.playSound(config.SOUND_UPDATE_MUSIC_DB_COMPLETED)
                self.wakeup()
        if keycode == config.BUTTON_ACTION:
            if clicks == 1:
                l.debug('action, 1 click')
                if self.sleeping == 1:
                    l.debug('>>> wake up !')
                    self.wakeup()
                else:
                    l.debug('>>> toggle !')
                    self.toggle()
            elif clicks == 2:
                l.debug('action, 2 clicks')
                if self.sleeping == 1:
                    self.wakeup()
                self.change_playlist()
            elif clicks == 3:
                l.debug('action, 3 clicks')
                l.debug('printing MPD status')
                status = self.mpd.status()
                print status
            elif self.isLongClick(clicks, holds):
                if self.sleeping == 0:
                    l.debug('Shutting down...')
                    self.shut_down()
            elif self.isExtraLongClick(clicks, holds):
                l.debug('action, EXTRA LONG CLICK')
                l.debug('>>> Resetting Network setup')                    
                self.resetNetwork()
            else:
                l.debug('action, ' + str(clicks) + ' clicks, ' + str(holds) + ' holds')
        elif keycode == config.BUTTON_VOL_UP:
            if clicks == 1:
                l.debug('volume up, 1 click')
                self.volume(+1)
            elif clicks > 1:
                l.debug('volume up, several clicks')
                l.debug('volume up, ' + str(clicks) + ' clicks, ' + str(holds) + ' holds')
                self.volume(+3)
            else:
                l.debug('volume up, other click')
                l.debug('volume up, ' + str(clicks) + ' clicks, ' + str(holds) + ' holds')
                #self.volume(+3)
        elif keycode == config.BUTTON_VOL_DOWN:
            l.debug('volume down, ' + str(clicks) + ' clicks, ' + str(holds) + ' holds')
            if clicks == 1:
                l.debug('volume down, 1 click')
                self.volume(-1)
            elif clicks > 1:
                l.debug('volume down, several clicks')
                l.debug('volume down, ' + str(clicks) + ' clicks, ' + str(holds) + ' holds')
                self.volume(-3)
            else:
                # WARNING: THIS EVENT WILL NOT BE TRIGGERED WHILE HOLDING THE BUTTON 
                l.debug('volume down, other click')
                l.debug('volume down, ' + str(clicks) + ' clicks, ' + str(holds) + ' holds')
                #self.volume(-3)
        if keycode == config.BUTTON_NEXT:
            if clicks == 1:
                l.debug('BUTTON_NEXT, 1 click')
                status = self.mpd.status()
                if status['state'] == 'play':
                    l.debug('>>> Next song !')
                    self.mpd.next()
        if keycode == config.BUTTON_PREV:
            if clicks == 1:
                l.debug('BUTTON_PREV, 1 click')
                status = self.mpd.status()
                if status['state'] == 'play':
                    l.debug('>>> Prev song !')
                    self.mpd.previous()
        if keycode == config.BUTTON_SEND_ANNA or keycode == config.BUTTON_SEND_ALBERTO:
            if clicks == 1:
                l.debug('BUTTON_SEND, 1 click')
                status = self.mpd.status()
                if status['state'] == 'play':
                    l.debug('>>> Sending current song !')
                    self.sendSong(keycode)
                else:
                    l.debug(' Nothing is playing !')                    
        if keycode == config.BUTTON_STOP:
            if clicks == 1:
                l.debug('BUTTON_STOP, 1 click')
                self.sleep()
        elif keycode == config.BUTTON_DEBUG:
            self.debug(clicks)
        elif keycode == config.BUTTON_QUIT:
            l.debug('quit, event')
            self.exit()

    def exit(self):
        self.buttons.exit()
        self.exit_event.set()


global_controller = None
#plug_ins = plugins.load_all()


@bottle.route('/')
def root():
    base_html = '<html><head><title>Castizer!</title></head><body>{}</body></html>'
    root_html = '''
        <h1>Dropbox plugin</h1>
        <ul>
        <li><a href="/castizer/plugins/dropbox/new">New Dropbox account</a>
        <li><a href="/castizer/plugins/dropbox/accounts">List existing accounts</a>
        </ul>'''
    return base_html.format(root_html)


@bottle.route('/plugins/<path:path>', method='ANY')
def plugins(path):
    if '/' in path:
        plugin_name, ppath = path.split('/', 1)
    else:
        plugin_name, ppath = path, ''
    try:
        LOG.debug(bottle.request.method + ' request to ' + plugin_name + ' -> ' + ppath)
        #return getattr(plug_ins[plugin_name], bottle.request.method)(ppath, bottle.request, bottle.response)
        plugin = plug_ins[plugin_name]
        method_f = getattr(plugin, bottle.request.method)
        return method_f(ppath, bottle.request, bottle.response)
    except KeyError:
        raise bottle.HTTPError(404, 'Plugin not found')
    except AttributeError as e:
        raise bottle.HTTPError(405, repr(e))

def main():
    global global_controller;
    global_controller = Controller()
    global_controller.start()
    if config.PLATFORM == 'castizer':
        #flup.server.fcgi.WSGIServer(bottle.default_app()).run()
        WSGIServer(bottle.default_app(), bindAddress="/tmp/fastcgi.python.socket").run()
    else:
        l = logging.getLogger('controller.event')
        l.debug('starting bottle...')
        # Reset the LED to ON, because during the boot up there is something that
        # overwrites it to off
        l.debug('main(): LED on')
        time.sleep(3)                
        global_controller.led.on()
        bottle.run(host='0.0.0.0', port=config.WEB_SERVER_PORT, debug=config.DEBUG)
    global_controller.exit()

if __name__ == '__main__':
    main()
