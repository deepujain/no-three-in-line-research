"""Synthetic process/file fixtures only; never opens research inputs."""
import argparse
import ctypes
import json
import os
from pathlib import Path
import resource
import signal
import time


def main():
    p = argparse.ArgumentParser(); p.add_argument('mode'); p.add_argument('--path', type=Path)
    a = p.parse_args()
    if a.mode == 'identity':
        print(json.dumps({'pid': os.getpid(), 'pgid': os.getpgrp(), 'sid': os.getsid(0)}))
    elif a.mode in ('stdout', 'stderr'):
        fd = 1 if a.mode == 'stdout' else 2
        while True: os.write(fd, b'x'*8192)
    elif a.mode == 'sleep':
        signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(10)
    elif a.mode == 'fork':
        child = os.fork()
        if child == 0:
            signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(10); os._exit(0)
        def reap(sig, frame):
            os.kill(child, signal.SIGKILL); os.waitpid(child, 0); raise SystemExit(0)
        signal.signal(signal.SIGTERM, reap)
        print(json.dumps({'child': child}), flush=True); time.sleep(10)
    elif a.mode in ('cap', 'fork_cap', 'exact_cap', 'partial_cap'):
        cap = 8*1024*1024; resource.setrlimit(resource.RLIMIT_FSIZE, (cap, cap))
        signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
        fd = os.open(a.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        # libc.write is a native write, with the limit enforced by the kernel.
        libc = ctypes.CDLL(None, use_errno=True); libc.write.restype = ctypes.c_ssize_t
        block = ctypes.create_string_buffer(b'a'*65536)
        def write(amount):
            return libc.write(fd, block, amount)
        for _ in range(cap//65536-1):
            if write(65536) != 65536: raise RuntimeError('short prefix')
        partial = None
        if a.mode == 'partial_cap':
            if write(65520) != 65520: raise RuntimeError('short near-cap prefix')
            partial = write(65536)
            if partial != 16: raise RuntimeError('partial cap write not enforced')
        elif write(65536) != 65536: raise RuntimeError('short final prefix')
        if a.mode == 'exact_cap':
            extra = None
        elif a.mode == 'fork_cap':
            child = os.fork()
            if child == 0:
                # Same open file descriptor and inherited hard/soft limit.
                result = write(65536)
                os._exit(0 if result == -1 and ctypes.get_errno() == 27 else 3)
            _, status = os.waitpid(child, 0); extra = status
            if status: raise RuntimeError('fork cap not enforced')
        else:
            extra = write(65536)
            if extra != -1 or ctypes.get_errno() != 27: raise RuntimeError('native cap not enforced')
        os.close(fd)
        print(json.dumps({'bytes': a.path.stat().st_size, 'limit': resource.getrlimit(resource.RLIMIT_FSIZE),
                          'extra': extra, 'partial': partial, 'cap_reached_is_incomplete': True}))
    else: raise ValueError('fixture mode')


if __name__ == '__main__': main()
