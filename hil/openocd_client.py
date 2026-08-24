"""Timeout-bounded OpenOCD TCL/telnet command client."""

from __future__ import annotations

import re
import socket

_PROMPT = b"> "


class OpenOcdError(RuntimeError):
    pass


class OpenOcdClient:
    def __init__(self, host: str = "127.0.0.1", port: int = 4444, timeout_s: float = 2.0):
        self._socket = socket.create_connection((host, port), timeout=timeout_s)
        self._socket.settimeout(timeout_s)
        self._read_until_prompt()

    def _read_until_prompt(self) -> str:
        chunks = bytearray()
        while not chunks.endswith(_PROMPT):
            data = self._socket.recv(4096)
            if not data:
                raise OpenOcdError("OpenOCD closed the connection")
            chunks.extend(data)
        return chunks[: -len(_PROMPT)].decode("utf-8", errors="replace")

    def command(self, command: str) -> str:
        self._socket.sendall(command.encode("ascii") + b"\n")
        return self._read_until_prompt()

    def read_word(self, address: int) -> int:
        output = self.command(f"mdw 0x{address:08X} 1")
        match = re.search(r"0x[0-9a-fA-F]+:\s+([0-9a-fA-F]{8})", output)
        if match is None:
            raise OpenOcdError(f"cannot parse mdw response: {output!r}")
        return int(match.group(1), 16)

    def read_register(self, name: str) -> int:
        output = self.command(f"reg {name}")
        match = re.search(r"0x([0-9a-fA-F]+)", output)
        if match is None:
            raise OpenOcdError(f"cannot parse register response: {output!r}")
        return int(match.group(1), 16)

    def close(self) -> None:
        self._socket.close()

    def __enter__(self) -> OpenOcdClient:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()
