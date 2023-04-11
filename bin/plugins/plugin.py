import argparse
from abc import ABC, abstractmethod

class DockerRunPlugin(ABC):
    
    @classmethod
    def addArguments(cls, parser: argparse.ArgumentParser):
        pass
    
    @classmethod
    @abstractmethod
    def getRunFlags(cls, args):
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def getExecFlags(cls, args):
        raise NotImplementedError()
