import argparse
import os
from typing import Dict, List

from .plugin import DockerRunPlugin


class DockerRunCorePlugin(DockerRunPlugin):
    
    @classmethod
    def addArguments(cls, parser: argparse.ArgumentParser):
        
        parser.add_argument("--no-rm", action="store_true", help="disable automatic container removal")
        parser.add_argument("--no-it", action="store_true", help="disable automatic interactive tty")
    
    @classmethod
    def getRunFlags(cls, args: Dict) -> List[str]:
        flags = []
        if not args["no_rm"]:
            flags += cls.removeFlags()
        if not args["no_it"]:
            flags += cls.interactiveFlags()
        return flags

    @classmethod
    def getExecFlags(cls, args: Dict) -> List[str]:
        return []

    @classmethod
    def removeFlags(cls):
        return ["--rm"]

    @classmethod
    def interactiveFlags(cls):
        return ["--interactive", "--tty"]
