import argparse
import os
import platform
import tempfile
from typing import Any, Dict, List

from utils import log, runCommand
from .plugin import DockerRunPlugin


class DockerRunCorePlugin(DockerRunPlugin):
    
    OS = platform.uname().system
    ARCH = platform.uname().machine
    
    @classmethod
    def addArguments(cls, parser: argparse.ArgumentParser):
        
        parser.add_argument("--no-rm", action="store_true", help="disable automatic container removal")
        parser.add_argument("--no-it", action="store_true", help="disable automatic interactive tty")
        parser.add_argument("--no-gpu", action="store_true", help="disable automatic GPU support")
        parser.add_argument("--no-x11", action="store_true", help="disable automatic X11 GUI forwarding")
    
    @classmethod
    def getRunFlags(cls, args: Dict[str, Any], unknown_args: List[str]) -> List[str]:
        flags = []
        if not args["no_rm"]:
            flags += cls.removeFlags()
        if not args["no_it"]:
            flags += cls.interactiveFlags()
        if not args["no_gpu"]:
            flags += cls.gpuSupportFlags()
        if not args["no_x11"]:
            gui_forwarding_kwargs = {}
            if "--network" in unknown_args:
                network_arg_index = unknown_args.index("--network") + 1
                if network_arg_index < len(unknown_args):
                    gui_forwarding_kwargs["docker_network"] = unknown_args[network_arg_index]
            flags += cls.x11GuiForwardingFlags(**gui_forwarding_kwargs)
        return flags

    @classmethod
    def getExecFlags(cls, args: Dict[str, Any], unknown_args: List[str]) -> List[str]:
        return []

    @classmethod
    def removeFlags(cls) -> List[str]:
        return ["--rm"]

    @classmethod
    def interactiveFlags(cls) -> List[str]:
        return ["--interactive", "--tty"]

    @classmethod
    def gpuSupportFlags(cls) -> List[str]:
        if cls.ARCH == "x86_64":
            return ["--gpus all"]
        elif cls.ARCH == "aarch64" and cls.OS == "Linux":
            return ["--runtime nvidia"]
        else:
            log(f"GPU not supported by `docker-run` on {cls.OS} with {cls.ARCH} architecture")
            return []

    @classmethod
    def x11GuiForwardingFlags(cls, docker_network: str = "bridge") -> List[str]:

        display = os.environ.get("DISPLAY")
        if display is None:
            return []

        xsock = "/tmp/.X11-unix"
        xauth = tempfile.NamedTemporaryFile(prefix='.docker.xauth.', delete=False).name
        xauth_display = display if cls.OS != "Darwin" else runCommand("ifconfig en0 | grep 'inet '")[0].split()[1] + ":0"
        xauth_output = "ffff" + runCommand(f"xauth nlist {xauth_display}")[0][4:]
        runCommand(f"xauth -f {xauth} nmerge - 2>/dev/null", input=xauth_output.encode())
        os.chmod(xauth, 0o777)

        if docker_network != "host" and not display.startswith(":"):
            display="172.17.0.1:" + display.split(":")[1]
        if cls.OS == "Darwin":
            display="host.docker.internal:" + display.split(":")[1]

        flags = []
        flags.append(f"--env DISPLAY={display}")
        flags.append(f"--env XAUTHORITY={xauth}")
        flags.append(f"--env QT_X11_NO_MITSHM=1")
        flags.append(f"--volume {xauth}:{xauth}")
        flags.append(f"--volume {xsock}:{xsock}")

        return flags
