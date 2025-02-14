import argparse
import os
import platform
import tempfile
from typing import Any, Dict, List

import pynvml

from docker_run.utils import log, runCommand
from docker_run.plugins.plugin import Plugin


class CorePlugin(Plugin):

    OS = platform.uname().system
    ARCH = platform.uname().machine

    @classmethod
    def addArguments(cls, parser: argparse.ArgumentParser):

        parser.add_argument("--no-rm", action="store_true", help="disable automatic container removal")
        parser.add_argument("--no-it", action="store_true", help="disable automatic interactive tty")
        parser.add_argument("--no-tz", action="store_true", help="disable automatic timezone")
        parser.add_argument("--no-gpu", action="store_true", help="disable automatic GPU support")
        parser.add_argument("--no-x11", action="store_true", help="disable automatic X11 GUI forwarding")
        parser.add_argument("--loc", action="store_true", help="enable automatic locale")
        parser.add_argument("--mwd", action="store_true", help="mount current directory at same path")

    @classmethod
    def getRunFlags(cls, args: Dict[str, Any], unknown_args: List[str]) -> List[str]:
        flags = []
        if not args["no_rm"]:
            flags += cls.removeFlags()
        if not args["no_it"]:
            flags += cls.interactiveFlags()
        if not args["no_tz"]:
            flags += cls.timezoneFlags()
        if not args["no_gpu"]:
            flags += cls.gpuSupportFlags()
        if not args["no_x11"]:
            gui_forwarding_kwargs = {}
            if "--network" in unknown_args:
                network_arg_index = unknown_args.index("--network") + 1
                if network_arg_index < len(unknown_args):
                    gui_forwarding_kwargs["docker_network"] = unknown_args[network_arg_index]
            flags += cls.x11GuiForwardingFlags(**gui_forwarding_kwargs)
        if args["loc"]:
            flags += cls.localeFlags()
        if args["mwd"]:
            flags += cls.currentDirMountFlags()
        return flags

    @classmethod
    def getExecFlags(cls, args: Dict[str, Any], unknown_args: List[str]) -> List[str]:
        flags = []
        if not args["no_it"]:
            flags += cls.interactiveFlags()
        return flags

    @classmethod
    def modifyFinalCommand(cls, cmd: List[str], args: Dict[str, Any], unknown_args: List[str]) -> List[str]:
        if "-v" in cmd or "--volume" in cmd:
            cmd = cls.resolveRelativeVolumeFlags(cmd)
            cmd = cls.fixSpacesInVolumeFlags(cmd)
        return cmd

    @classmethod
    def removeFlags(cls) -> List[str]:
        return ["--rm"]

    @classmethod
    def interactiveFlags(cls) -> List[str]:
        return ["--interactive", "--tty"]

    @classmethod
    def timezoneFlags(cls) -> List[str]:
        flags = []
        if os.path.isfile("/etc/timezone"):
            flags.append("--volume /etc/timezone:/etc/timezone:ro")
        if os.path.isfile("/etc/localtime"):
            flags.append("--volume /etc/localtime:/etc/localtime:ro")
        return flags

    @classmethod
    def localeFlags(cls) -> List[str]:
        return ["--env LANG", "--env LANGUAGE", "--env LC_ALL"]

    @classmethod
    def gpuSupportFlags(cls) -> List[str]:
        n_gpus = 0
        try:
            pynvml.nvmlInit()
            n_gpus = pynvml.nvmlDeviceGetCount()
        except pynvml.NVMLError:
            pass
        if n_gpus > 0:
            if cls.ARCH == "x86_64":
                return ["--gpus all"]
            elif cls.ARCH == "aarch64" and cls.OS == "Linux":
                return ["--runtime nvidia"]
            else:
                log(f"GPU not supported by `docker-run` on {cls.OS} with {cls.ARCH} architecture")
                return []
        else:
            log(f"No GPU detected")
            return []

    @classmethod
    def x11GuiForwardingFlags(cls, docker_network: str = "bridge") -> List[str]:

        display = os.environ.get("DISPLAY")
        if display is None:
            return []

        if cls.OS == "Darwin":
            runCommand(f"xhost +local:")

        xsock = "/tmp/.X11-unix"
        xauth = tempfile.NamedTemporaryFile(prefix='.docker.xauth.', delete=False).name
        xauth_display = display if cls.OS != "Darwin" else runCommand("ifconfig en0 | grep 'inet '")[0].split()[1] + ":0"
        xauth_output = "ffff" + runCommand(f"xauth nlist {xauth_display}")[0][4:]
        runCommand(f"xauth -f {xauth} nmerge - 2>/dev/null", input=xauth_output.encode())
        os.chmod(xauth, 0o777)

        if docker_network != "host" and not display.startswith(":"):
            display = "172.17.0.1:" + display.split(":")[1]
        if cls.OS == "Darwin":
            display = "host.docker.internal:" + display.split(":")[1]

        flags = []
        flags.append(f"--env DISPLAY={display}")
        flags.append(f"--env XAUTHORITY={xauth}")
        flags.append(f"--env QT_X11_NO_MITSHM=1")
        flags.append(f"--volume {xauth}:{xauth}")
        flags.append(f"--volume {xsock}:{xsock}")

        return flags

    @classmethod
    def currentDirMountFlags(cls) -> List[str]:
        cwd = os.getcwd().replace(" ", "\\ ")
        return [f"--volume {cwd}:{cwd}", f"--workdir {cwd}"]

    @classmethod
    def resolveRelativeVolumeFlags(cls, cmd: List[str]) -> List[str]:
        for i, arg in enumerate(cmd):
            if arg in ["-v", "--volume"]:
                mount_path = cmd[i + 1].split(":")[0]
                if mount_path.startswith("."):
                    absolute_mount_path = os.path.abspath(mount_path)
                    cmd[i + 1] = absolute_mount_path + cmd[i + 1][len(mount_path):]
        return cmd

    @classmethod
    def fixSpacesInVolumeFlags(cls, cmd: List[str]) -> List[str]:
        for i, arg in enumerate(cmd):
            if arg in ["-v", "--volume"]:
                cmd[i + 1] = cmd[i + 1].replace(" ", "\\ ")
        return cmd