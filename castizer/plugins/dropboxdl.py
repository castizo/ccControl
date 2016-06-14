import castizer

import collections
import contextlib
import cPickle
#import gdbm
import logging
import os
import Queue
import shutil
import threading
import time
import urllib

import bottle
#import dropbox


APP_KEY = 'q52q9210kcismsg'
APP_SECRET = 'f0gibh5gq12zrjx'
AUTH_URL = 'https://ssl.castizer.com/dropbox-auth/start?key={}&secret={}&redirect={}'

#DATABASE = os.path.join(castizer.config.DATABASES_PATH, 'dropbox-gdbm.db')
DOWNLOAD_PATH = os.path.join(castizer.config.AUDIOFILES_PATH, 'dropbox')
DELTA_INTERVAL = 60 * 5 

LOG = logging.getLogger('Dropbox plugin')


class ExitException(Exception): pass


Account = collections.namedtuple('Account', 'uid, token, cursor, updated')


class Model(collections.MutableMapping):
    '''
    Model wraps a shelve database so that it behaves like a dict while
    keeping the strict constraints that some of the actual DB implementations
    need. To that end, Shelve will allow only one thread to open the file
    and will close it immediately after any operation, to keep the DB synced
    on disk (as much as possible).
    '''
    
    def __init__(self, filename):
        self.lock = threading.Semaphore()
        self.db = filename
        self.d = {}
        with self.lock, contextlib.closing(gdbm.open(self.db, 'c')) as sd:
            for key in sd.keys():
                self.d[key] = Account(*cPickle.loads(sd[key]))

    def __getitem__(self, key):
        with self.lock:
            return self.d[key]
    
    def __setitem__(self, key, value):
        with self.lock, contextlib.closing(gdbm.open(self.db, 'w')) as sd:
            self.d[key] = value
            sd[key] = cPickle.dumps(tuple(value))
    
    def __delitem__(self, key):
        with self.lock, contextlib.closing(gdbm.open(self.db, 'w')) as sd:
            del self.d[key]
            del sd[key]

    def __contains__(self, key):
        with self.lock:
            return key in self.d
    
    def __iter__(self):
        with self.lock:
            return iter(self.d.keys())
    
    def __len__(self):
        with self.lock:
            return len(self.d)


class FS(object):
    
    @staticmethod
    def delete(path):
        if os.path.exists(path):
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
    
    @staticmethod
    def force_dir(path):
        if os.path.isfile(path):
            os.remove(path)
        if not os.path.exists(path):
            os.makedirs(path)


class DropboxPlugin(castizer.plugins.Plugin):

    NAME = 'dropbox'
    BUFFER_BYTES = 2048
    QUEUE_WAIT = 10

    def __init__(self):
        super(DropboxPlugin, self).__init__()
        self.accounts = Model(DATABASE)
        self.queue = Queue.Queue()
        self.daemon = True
        FS.force_dir(DOWNLOAD_PATH)

    @staticmethod
    def _get_path(account, dropbox_path=''):
        p = os.sep.join((DOWNLOAD_PATH, account.uid, dropbox_path))
        return os.path.normpath(p)

    def _process_message(self, msg):
        cmd = msg[0]
        if cmd == 'exit':
            raise ExitException()
        elif cmd == 'delete':
            uid = msg[1]
            account = self.accounts[uid]
            FS.delete(self._get_path(account))
            del self.accounts[uid]
    
    def _watch_queue(self, wait=0):
        '''
        If wait > 0, wait on the queue and process messages until
        'wait' secs have passed. Else, exit when the queue is empty.
        '''
        initial = time.time() if wait > 0 else 0
        while True:
            timeout = wait - (time.time() - initial) if wait > 0 else 0
            try:
                msg = self.queue.get(timeout > 0, timeout)
            except Queue.Empty:
                return
            try:
                self._process_message(msg)
            finally:
                self.queue.task_done()
    
    def _download(self, account, client, dropbox_path, local_path):
        '''
        Download a file from Dropbox, deleting whatever existed before with the
        same name.
        '''
        LOG.debug('UID: ' + account.uid + ', downloading: ' + dropbox_path)#FIXME
        FS.delete(local_path)
        request = client.get_file(dropbox_path)
        buf = None
        with open(local_path, 'w') as f:
            while buf != '' and account.uid in self.accounts:
                buf = request.read(self.BUFFER_BYTES)
                f.write(buf)
                self._watch_queue(0)

    def _delta(self, account):
        '''
        See: https://www.dropbox.com/static/developers/dropbox-python-sdk-1.6-docs/index.html#dropbox.client.DropboxClient.delta
        '''
        account_path = self._get_path(account)
        client = dropbox.client.DropboxClient(account.token)
        delta = client.delta(account.cursor)
        LOG.debug('DELTA: ' + repr(delta))#FIXME
        if delta['reset']: # If 'reset', clear base dir before anything
            FS.delete(account_path)
        FS.force_dir(account_path)
        for dropbox_path, metadata in sorted(delta['entries']):
            local_path = self._get_path(account, dropbox_path)
            if metadata['is_dir']: # New entry is a folder
                FS.force_dir(local_path)
            elif metadata['mime_type'].startswith('audio/'): # Entry is an audio file
                self._download(account, client, dropbox_path, local_path)
        # Save cursor
        account = account._replace(cursor=delta['cursor'])
        # If 'has_more' we have to call delta again, don't store last update time
        if not delta['has_more']:
            account = account._replace(updated=time.time())
        self.accounts[account.uid] = account
        LOG.debug('UID: ' + account.uid + ', last updated: ' + str(account.updated))#FIXME

    def run(self):
        try:
            while True:
                for account in self.accounts.values():
                    now = time.time()
                    scheduled = account.updated + DELTA_INTERVAL
                    #LOG.debug('UID: ' + account.uid + ', now: ' + str(now) + ', scheduled: ' + str(scheduled))#FIXME
                    if now > scheduled:
                        self._delta(account)
                self._watch_queue(self.QUEUE_WAIT)
        except ExitException:
            pass

    def exit(self):
        self.queue.put(('exit',))

    def delete_account(self, uid):
        self.queue.put(('delete', uid))
    
    def create_account(self, token, uid=None):
        if uid == None:
            client = dropbox.client.DropboxClient(token)
            uid = str(client.account_info()['uid'])
        if uid in self.accounts:
            return
        account = Account(uid=uid, token=token, cursor=None, updated=0)
        self.accounts[uid] = account

    def GET(self, path, request, response):
        if path == 'new':
            redir = urllib.quote(request.url + '/callback')
            auth_url = AUTH_URL.format(APP_KEY, APP_SECRET, redir)
            return bottle.redirect(auth_url)
        elif path == 'accounts':
            html = '''<form name="delete_accounts" action="./delete_accounts"
                      method="post"> {checkboxes}
                      <input type="submit" value="Delete"></form>'''
            checkbox = '<input type="checkbox" name="{uid}">{text}<br>'
            checkboxes = ''
            for account in self.accounts.values():
                client = dropbox.client.DropboxClient(account.token)
                info = client.account_info()
                display_name, uid = info['display_name'], str(info['uid'])
                checkboxes += checkbox.format(uid=uid, 
                    text=display_name + ' (' + uid + ')')
            return html.format(checkboxes=checkboxes)
        elif path == 'new/callback':
            token = request.query.get('access_token')
            uid = request.query.get('uid', None)
            self.create_account(token, uid)
            return 'OK'#FIXME
        return 'Hello from the Dropbox plugin!'

    def POST(self, path, request, response):
        if path == 'delete_accounts':
            for uid in request.forms.keys():
                self.delete_account(uid)
            return 'OK'#FIXME
        return 'Hello from the Dropbox plugin!'
