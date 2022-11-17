from abc import abstractmethod

class Plugin(object):
    def __init__(self, infos):
        self.infos = infos

    @abstractmethod
    def load(self):
        """Code to execute on every plugin import
        """
        return

    @abstractmethod
    def initialize(self):
        """Code to execute on first plugin import
        """
        return

    @abstractmethod
    def remove(self):
        """Code to execute on plugin deletion
        """
        return