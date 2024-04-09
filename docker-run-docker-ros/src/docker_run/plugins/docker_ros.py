import argparse
import os
from typing import Any, Dict, List

from docker_run.utils import runCommand
from docker_run.plugins.plugin import Plugin


__version__ = "1.0.4"


class DockerRosPlugin(Plugin):

    WORKSPACE = "/docker-ros/ws"
    TARGET_MOUNT = f"{WORKSPACE}/src/target"

    @classmethod
    def addArguments(cls, parser: argparse.ArgumentParser):

        prefix = "[docker-ros]"

        parser.add_argument("--no-user", action="store_true", help=f"{prefix} disable passing local UID/GID into container")
        parser.add_argument("--mws", action="store_true", help=f"{prefix} mount current directory into ROS workspace at `{cls.TARGET_MOUNT}`")

    @classmethod
    def getRunFlags(cls, args: Dict[str, Any], unknown_args: List[str]) -> List[str]:
        flags = []
        if not args["no_user"]:
            flags += cls.userFlags()
        if args["mws"]:
            flags += cls.currentDirMountWorkspaceFlags()
        return flags

    @classmethod
    def getExecFlags(cls, args: Dict[str, Any], unknown_args: List[str]) -> List[str]:
        flags = []
        is_docker_user = False
        docker_uid = runCommand(f"docker exec {args['name']} printenv DOCKER_UID || true")[0][:-1]
        if len(docker_uid) > 0:
            is_docker_user = (len(runCommand(f"docker exec {args['name']} id -u {docker_uid} || true")[0][:-1]) > 0)
        if not args["no_user"] and is_docker_user:
            flags += cls.userExecFlags(docker_uid)
        return flags

    @classmethod
    def userFlags(cls) -> List[str]:
        return [f"--env DOCKER_UID={os.getuid()}", f"--env DOCKER_GID={os.getgid()}"]

    @classmethod
    def userExecFlags(cls, user: str) -> List[str]:
        return [f"--user {user}"]

    @classmethod
    def currentDirMountWorkspaceFlags(cls) -> List[str]:
        cwd = os.getcwd().replace(" ", "\\ ")
        return [f"--volume {cwd}:{cls.TARGET_MOUNT}", f"--workdir {cls.WORKSPACE}"]
