import argparse
import os
from typing import Any, Dict, List

from utils import runCommand
from .plugin import Plugin


class DockerRosPlugin(Plugin):
    
    TARGET_MOUNT = "/docker-ros/ws/src/target"
    
    @classmethod
    def addArguments(cls, parser: argparse.ArgumentParser):
        
        parser.add_argument("--no-user", action="store_true", help="disable passing local UID/GID into container")
        parser.add_argument("--mwd", action="store_true", help=f"mount current directory into `{cls.TARGET_MOUNT}`")
    
    @classmethod
    def getRunFlags(cls, args: Dict[str, Any], unknown_args: List[str]) -> List[str]:
        flags = []
        if not args["no_user"]:
            flags += cls.userFlags()
        if args["mwd"]:
            flags += cls.currentDirMountFlags()
        return flags

    @classmethod
    def getExecFlags(cls, args: Dict[str, Any], unknown_args: List[str]) -> List[str]:
        flags = []
        if not args["no_user"] and runCommand(f"docker exec {args['name']} bash -c 'echo $DOCKER_ROS'")[0][:-1] == "1":
            flags += cls.userExecFlags()
        return flags

    @classmethod
    def userFlags(cls) -> List[str]:
        return [f"--env DOCKER_UID={os.getuid()}", f"--env DOCKER_GID={os.getgid()}"]

    @classmethod
    def userExecFlags(cls) -> List[str]:
        return [f"--user {os.getuid()}"]

    @classmethod
    def currentDirMountFlags(cls) -> List[str]:
        return [f"--volume {os.getcwd()}:{cls.TARGET_MOUNT}"]
