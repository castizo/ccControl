# updater.update() checks for available updates. Dows the first one, decompresses it, and sets the flag "update"
# return value:
#   0: no updates available
#   n>0:    Success. n indicates the number of updates available
#   n<0:    Fail: An error occurred trying to download the new update.
# n indicates the number of updates available BUT... we may also return a -1 for some kind of errors...

#import MySQLdb
import os
#import glob

global_servername = "pc-pablo.dacya.ucm.es"
#global_update_flag = "/root/config/update"
#global_update_folder = "/root/update"
# Should it go into the ./config/update folder?
global_update_flag = "../update/update"
global_update_folder = "../update"

class Updater(object):

    def __init__(self, server="localhost"):
        self.server = server

    def getCurrentVersion(self):
        global global_update_folder
        
        filename_version = 'current_version'
        filename_version_path = global_update_folder + "/" + filename_version
        print "Reading current version from %s" % (filename_version_path)

        try:
            file_handler = open(filename_version_path, "r")
        except IOError, e:
            print e
            print 'Current version not found'

        #print "Version succesfully got!"
        current_version_string = file_handler.readline()
        file_handler.close()
        current_version = int(current_version_string)
        print "Current version: <" + str(current_version) + ">"
        return current_version

    def getNewestVersion(self):
        global global_update_folder
        
        filename_version = 'repository_version'
        filename_version_path = global_update_folder + "/" + filename_version
        url = "http://" + self.server + "/" + filename_version 
        print "Download %s as %s" % (url, filename_version_path)
        command = "rm -rf " + filename_version_path
        os.system(command)
        try: 
            command = "wget -P " + global_update_folder + " " + url
            #command = "ping " + self.server + " "
            wget_status = os.system(command)
        except: 
            print "castizer DEBUG: " + sys.exc_info()[1] 

        if wget_status == 0:
            print "Repository version succesfully got!"
            file_handler = open(filename_version_path, "r")
            newest_version_string = file_handler.readline()
            newest_version = int(newest_version_string)
            #print "Newest version: <" + str(newest_version) + ">"
            file_handler.close()
            return newest_version
        else:
            print "FAIL!"
            return -1

            current_version = 1
            print "server version:", newest_version

    def printNewestVersion(self):
        
        newest_version = self.getNewestVersion()
        print "Newest version: <" + str(newest_version) + ">"

    def dowUpdate(self, filename):

        url = "http://" + self.server + "/" + filename
        print "Download %s as %s" % (url, filename)
        command = "rm -rf " + filename
        os.system(command)
        try: 
            command = "wget -P " + global_update_folder + " " + url
            wget_status = os.system(command)
        except: 
            print "castizer DEBUG: " + sys.exc_info()[1] 

        if wget_status == 0:
            print "SUCCESS!"
            return 0
        else:
            print "FAIL!"
            return -1


    def update(self):

        global global_update_flag
        global global_update_folder

        newest_version = self.getNewestVersion()
        if newest_version <= 0:
            print "ERROR getting the newest version"
            return -1
        current_version = self.getCurrentVersion()
        if current_version <= 0:
            print "ERROR getting the current version"
            return -1
        
        num_available_updates = newest_version - current_version
        print "Available updates: ", num_available_updates
        
        if num_available_updates == 0:
            return 0

        # select the next update
        next_version = current_version + 1
        print "Next version: ", next_version
        #castizer_update_0000.tar.gz  
        filename = 'castizer_update_' + str(next_version) + '.tar.gz'
        print ">>> UPDATING to version:", next_version, "FILENAME:", filename

        if self.dowUpdate(filename) < 0:
            print "Error downloading update"
            return -num_available_updates

        print ">>> Uncompressing update... "
        full_filename = global_update_folder + "/" + filename
        command = "tar -xzvf " + full_filename + " -C " + global_update_folder
        command_status = os.system(command)
        if command_status < 0:
            print "Error decompressing update"
            return -1
        command = "rm -rf " + full_filename
        os.system(command)

        print ">>> Setting update flag... "
        command = "echo " + filename + " > " + global_update_flag
        print command
        command_exit_code = os.system(command)
        if command_exit_code != 0:
            return -1
        print ">>> Rebooting... "
        return num_available_updates

    
def main():

    global global_servername

    updater = Updater(global_servername)
    #updater.getCurrentVersion()
    #updater.printNewestVersion()
    exit_code = updater.update()

    print "updater.update() exited with code <" + str(exit_code) + ">" 
    print "END OF PROGRAM."


if __name__ == "__main__":
    main()
    