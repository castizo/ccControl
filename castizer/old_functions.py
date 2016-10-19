    # Sends the current playing song to either local or remote samba folder
    def sendSongSamba(self, person):
        l = logging.getLogger('controller.event')
        self.getCurrentSongURL()
        print ('Song URL: ', config.current_song_URL)
        self.saveSoundContext()
        self.playSound(config.SOUND_SENDING_SONG_TO)
        if (person == config.BUTTON_SEND_ANNA):
            self.playSound(config.SOUND_ANNA)
            config.sendTo = config.C_SAMBA_SERVER_REMOTE
            self.usersamba = config.C_USERSAMBA_REMOTE
        elif (person == config.BUTTON_SEND_ALBERTO):
            self.playSound(config.SOUND_ALBERTO)
            config.sendTo = config.C_SAMBA_SERVER_LOCAL
            self.usersamba = config.C_USERSAMBA_LOCAL
        else:
            l.debug('ERROR: main.sendSong')                    
            self.playSound(config.SOUND_WARNING_ALARM)

        self.createJson()

        #command = "smbclient //" + self.sendTo + "/cc_samba -c 'md \"" + path + "\";  put \"" + config.MUSIC_PATH + "/" + config.current_song_URL + "\" \"" + config.current_song_URL + "\"' -U " + self.usersamba + " pass"
        command = "smbclient //" + config.sendTo + "/cc_samba -c 'put \"" + config.MUSIC_PATH + "/" + config.current_song_URL + "\" \"" + config.C_INCOMING_FOLDER + "/" + config.current_song_file + "\"; put \"" + config.JSON_OUTFILE + "\" \"" + config.C_INCOMING_FOLDER + "/" + config.JSON_OUTFILE + "\"' -U " + self.usersamba + " pass"
        #command_send_json_file = "smbclient //" + config.sendTo + "/cc_samba -c '' -U " + self.usersamba + " pass"
        print 'COMMAND: ', command
        #print 'COMMAND command_send_json_file: ', command_send_json_file
        
        t = threading.Thread(target=self.doSendSong, args = (self.queue_do, command))
        t.start()
        l.debug('Created new thread to send the song in background')

        self.restoreSoundContext()


    # TODO: this function should be called in a periodic basis
    # Setup a timer
    # A function checks if the file exists every 1 minute, for instance
    #     if it exists, launches a new background process to get it
    #     once finished, blink the LED to notify user !
    def checkForIncomingSongsSamba(self):

        l = logging.getLogger('controller.event')

        json_infile = config.SAMBA_PATH + "/" + config.C_INCOMING_FOLDER + "/" + config.JSON_OUTFILE
        #check if there is incoming music
        if os.path.isfile(json_infile):
            print 'Incoming Song Available !'
            self.incoming_songs = True
            print 'TODO: blink LED !'
            l.debug('JSON file exists !')
        else:
            print 'No Songs Available !'
            l.debug('JSON file does not exist !')
            return

    def getIncomingSongSamba(self):
                
        l = logging.getLogger('controller.event')

        json_infile = config.SAMBA_PATH + "/" + config.C_INCOMING_FOLDER + "/" + config.JSON_OUTFILE
        #check if there is incoming music
        if os.path.isfile(json_infile):
            print 'Incoming Song Available !'
            l.debug('JSON file exists !')
        else:
            print 'No Songs Available !'
            l.debug('JSON file does not exist !')
            return
    
        #save sound Context
        try:
            self.mpd.rm('pl_current')
        except mpd.CommandError: 
            print 'There was no pl_current playlist'        
        self.mpd.save('pl_current')

        # Reading data back
        with open(json_infile, 'r') as infile:
            json_data = json.load(infile)
        
        print "************************"

        print "Number of songs: " + str(json_data['incoming'])
        for song in json_data['songs']:   
            print "Sender: " + str(song['sender']) + " URL: " + str(song['url'])
            config.received_song_url =  str(song['url'])

        print "************************"
        
        # copy received song from incoming to received folder
        command = "mv \"" + config.SAMBA_PATH + "/" + config.C_INCOMING_FOLDER + "/" + config.received_song_url + "\" " + config.MUSIC_PATH + "/" + config.C_RECEIVED_FOLDER + "/"
        print 'COMMAND: ', command
        try: 
            command_status = os.system(command)
        except: 
            l.debug('receiveSong(): ERROR during file move')
            l.debug('receiveSong(): ERROR1')
            self.playSound(config.SOUND_WARNING_ALARM)
            return -1
        if command_status == 0:
            l.debug('receiveSong() file moved succesfully !')
            self.playSound(config.SOUND_SEND_OK)
            #self.playSound(config.SOUND_RESET_NETWORK_COMPLETED)
            #l.debug('resetNetwork(): END')
        else:
            l.debug('receiveSong(): File already existed. For the momment we dont care.')
            self.playSound(config.SOUND_SEND_OK)
 
        #update mpd Library
        l.debug('>>> Updating MUSIC DataBase')                    
        time.sleep(1)
        self.mpd.update()
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
 
#         #play song
#         #self.playSound(config.C_RECEIVED_FOLDER + "/" + config.received_song_url)

        song_uri = config.C_RECEIVED_FOLDER + "/" + config.received_song_url
          
        #restore sound context
        print('restoring context...')
        self.mpd.clear()
        try:
            self.mpd.load('pl_current')
        except mpd.CommandError: 
            print 'There was no pl_current playlist'
            self.change_playlist()
            return
 
        self.mpd.addid(song_uri, 0)
        l.debug('Adding received song in the first position of the playlist')        
         
        l.debug('Resume playing from received song')        
        self.mpd.play(0)

        #TODO: go to awake status ???
                
        # remove json file
        command = "rm " + json_infile
        print 'COMMAND: ', command
        try: 
            command_status = os.system(command)
        except: 
            l.debug('readJson(): ERROR during file removal')
            self.playSound(config.SOUND_WARNING_ALARM)
            return -1
        if command_status == 0:
            l.debug('readJson(): JSON file succesfully removed')
        else:
            l.debug('readJson(): ERROR during file removal')
            self.playSound(config.SOUND_WARNING_ALARM)
            return -1

        self.incoming_songs = False
        print 'TODO: stop LED blinking !'

#        TOFUTURE: create special status to know that we are in special mode...
         

