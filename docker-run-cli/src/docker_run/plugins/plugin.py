import argparse
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class Plugin(ABC):

    @classmethod
    def addArguments(cls, parser: argparse.ArgumentParser):
        pass

    @classmethod
    @abstractmethod
    def getRunFlags(cls, args: Dict[str, Any], unknown_args: List[str]) -> List[str]:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def getExecFlags(cls, args: Dict[str, Any], unknown_args: List[str]) -> List[str]:
        raise NotImplementedError()

    @classmethod
    def modifyFinalCommand(cls, cmd: List[str], args: Dict[str, Any], unknown_args: List[str]) -> List[str]:
        return cmd
