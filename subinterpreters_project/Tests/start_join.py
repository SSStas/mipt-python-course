#!/usr/bin/env python3
import sys
import threading
import multiprocessing as mp

try:
    import pyperf
except ImportError:
    pyperf = None

try:
    from concurrent import interpreters
except ImportError:
    interpreters = None


def empty_func():
    pass


def bench_thread() -> None:
    t = threading.Thread(target=empty_func)
    t.start()
    t.join()


def bench_mp() -> None:
    ctx = mp.get_context("spawn")
    p = ctx.Process(target=empty_func)
    p.start()
    p.join()


def bench_subinterp() -> None:
    interp = interpreters.create()
    try:
        t = interp.call_in_thread(empty_func)
        t.join()
    finally:
        interp.close()


def main() -> int:
    if (pyperf is None):
        print("Error: pyperf is not installed. Install: python -m pip install pyperf", file=sys.stderr)
        sys.exit(1)

    if (interpreters is None):
        print(
            "Error: subinterpreters are not available in this Python",
            "Requires Python 3.14+ (concurrent.interpreters)",
            f"Current version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            file=sys.stderr,
            sep="\n",
        )
        sys.exit(1)
    
    runner = pyperf.Runner()

    runner.bench_func("threads", bench_thread)
    runner.bench_func("multiprocess", bench_mp)
    runner.bench_func("subinterp", bench_subinterp)

if __name__ == "__main__":
    main()
