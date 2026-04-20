import subprocess
from typing import Optional, Union

from aicrate.logger import logger


class ExecutionError(Exception):
    def __init__(self, code: int, out: str, err: str) -> None:
        self.code = code
        self.out = out
        self.err = err

    def __str__(self):
        return f"Command failed with rc={self.code}. Stdout:\n{self.out}\nStderr:\n{self.err}\n"


class Command:
    def __init__(self, args: Union[str, list[str]], shell: bool = True) -> None:
        self.args = args
        self.shell = shell

    def run(self, inputs: list[str], **kwargs):
        process = subprocess.Popen(
            self.args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            **kwargs,
        )
        logger.debug(f"Executing of command '{process.args}' started")
        if not inputs:
            out, err = process.communicate()
        else:
            for input in inputs:
                out, err = process.communicate(input=f"{input}\n")

        logger.debug(
            f"Executing of command '{process.args}' finished with result '{process.returncode}',"
            f" stdout '{out}', stderr '{err}'"
        )

        if process.returncode != 0:
            raise ExecutionError(process.returncode, out, err)

        return out


def run_cmd_with_error_handler(
    args: list[str], inputs: list[str], error_msg: str
) -> str:
    try:
        cmd = Command(args=args)
        return cmd.run(inputs)
    except ExecutionError as ex:
        logger.error(error_msg)
        raise ex


def run_cmd(
    args: list[str],
    inputs: list[str],
    supress_error: bool = False,
) -> Optional[str]:
    try:
        cmd = Command(args=args)
        return cmd.run(inputs)
    except ExecutionError as ex:
        if not supress_error:
            raise ex
