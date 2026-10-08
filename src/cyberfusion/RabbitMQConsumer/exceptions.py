"""Exceptions."""

from dataclasses import dataclass


class VirtualHostNotExistsError(Exception):
    """Virtual host doesn't exist."""

    pass


@dataclass
class RpcCallFailedError(Exception):
    rc: int
    stdout: str
    stderr: str

    def __str__(self) -> str:
        return f"""Call failed with RC {self.rc}

Stdout: {self.stdout}
Stderr: {self.stderr}
"""
