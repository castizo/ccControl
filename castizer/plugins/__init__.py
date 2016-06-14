import importlib
import logging
import pkgutil
import threading


LOG = logging.getLogger('plugins loader')


class Plugin(threading.Thread):
    NAME = ''


def load_all():
    # First import all modules under plugins, therefore populating
    # Plugin.__subclasses__() automatically as every plugin should
    # contain a class that derives from Plugin
    for _, name, ispkg in pkgutil.walk_packages(__path__, __name__ + '.'):
        if not ispkg:
            importlib.import_module(name)
    # Then instantiate, start and store a reference to every plugin
    plugins = {}
    for Cls in Plugin.__subclasses__():
        if Cls.NAME:
            plugin = Cls()
            plugin.start()
            plugins[Cls.NAME] = plugin
    # Finally return a reference to the plugins, indexed by 'NAME'
    return plugins
