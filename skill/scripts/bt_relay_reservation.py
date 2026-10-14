"""Exclusive wrapper successor publication and cleanup of owned inodes only."""
from __future__ import annotations

import contextlib
import os
import uuid
from pathlib import Path

import bt_relay as relay


class ReservationError(ValueError):
    """Another helper owns the wrapper reservation or successor."""


def _remove_owned(path: Path, inode: tuple[int, int] | None) -> None:
    try:
        stat = path.lstat()
        if inode == (stat.st_dev, stat.st_ino):
            path.unlink()
    except FileNotFoundError:
        pass


class Reservation:
    def __init__(self, path: Path):
        self.path = path
        self.inode: tuple[int, int] | None = None

    def publish(self, text: str) -> None:
        temporary = self.path.with_name(self.path.name + '.' + uuid.uuid4().hex + '.tmp')
        relay.write_private(temporary, text)
        try:
            stat = temporary.stat()
            self.inode = (stat.st_dev, stat.st_ino)
            # link publishes the entire private inode atomically and refuses replacement.
            os.link(temporary, self.path)
        except FileExistsError as exc:
            raise ReservationError('a successor is already prepared for this wrapper') from exc
        finally:
            temporary.unlink()


@contextlib.contextmanager
def reserve(path: Path):
    relay.private_dir(path.parent)
    lock = path.with_name(path.name + '.lock')
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise ReservationError('wrapper successor reservation is held; inspect it before manual recovery') from exc
    stat = os.fstat(fd)
    os.close(fd)
    reservation = Reservation(path)
    try:
        if path.exists():
            raise ReservationError('a successor is already prepared for this wrapper')
        yield reservation
    except BaseException:
        _remove_owned(path, reservation.inode)
        raise
    finally:
        _remove_owned(lock, (stat.st_dev, stat.st_ino))
