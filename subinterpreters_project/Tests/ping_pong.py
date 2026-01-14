import sys
import queue
import threading
import multiprocessing as mp
from typing import Callable, Tuple

try:
    import pyperf
except ImportError:
    pyperf = None

try:
    from concurrent import interpreters
except ImportError:
    interpreters = None


# threads (noGIL speedup on 3.14t)

def thread_worker(q_in, q_out, num_bytes) -> None:
    reply = b"b" * num_bytes
    while (True):
        msg = q_in.get()
        if (msg is None):
            break
        q_out.put(reply)


def make_threads_bench(num_bytes: int) -> Tuple[Callable[[int], float], Callable[[], None]]:
    q_in = queue.Queue()
    q_out = queue.Queue()

    t = threading.Thread(target=thread_worker, args=(q_in, q_out, num_bytes))
    t.start()

    payload = b"a" * num_bytes

    def bench(loop: int) -> float:
        start = pyperf.perf_counter()
        for _ in range(loop):
            q_in.put(payload)
            q_out.get()
        end = pyperf.perf_counter()
        return (end - start)

    def cleanup() -> None:
        q_in.put(None)
        t.join()

    return (bench, cleanup)


# multiprocessing

def mp_worker(q_in, q_out, num_bytes) -> None:
    reply = b"b" * num_bytes
    while (True):
        msg = q_in.get()
        if (msg is None):
            break
        q_out.put(reply)


def make_mp_bench(num_bytes: int) -> Tuple[Callable[[int], float], Callable[[], None]]:
    ctx = mp.get_context("spawn")
    q_in = ctx.Queue()
    q_out = ctx.Queue()

    p = ctx.Process(target=mp_worker, args=(q_in, q_out, num_bytes))
    p.start()

    payload = b"a" * num_bytes

    def bench(loop: int) -> float:
        start = pyperf.perf_counter()
        for _ in range(loop):
            q_in.put(payload)
            q_out.get()
        end = pyperf.perf_counter()
        return (end - start)

    def cleanup() -> None:
        q_in.put(None)
        p.join()
        q_in.close()
        q_in.join_thread()
        q_out.close()
        q_out.join_thread()

    return (bench, cleanup)


# subinterpreters

def subinterp_worker(q_in, q_out, num_bytes) -> None:
    reply = b"b" * num_bytes
    while (True):
        msg = q_in.get()
        if (msg is None):
            break
        q_out.put(reply)


def make_subinterp_bench(num_bytes: int) -> Tuple[Callable[[int], float], Callable[[], None]]:
    interp = interpreters.create()
    q_in = interpreters.create_queue()
    q_out = interpreters.create_queue()

    t = interp.call_in_thread(subinterp_worker, q_in, q_out, num_bytes)

    payload = b"a" * num_bytes

    def bench(loop: int) -> float:
        start = pyperf.perf_counter()
        for _ in range(loop):
            q_in.put(payload)
            q_out.get()
        end = pyperf.perf_counter()
        return (end - start)

    def cleanup() -> None:
        q_in.put(None)
        t.join()
        interp.close()

    return (bench, cleanup)


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

    for num_bytes in [1, 1000, 100000, 1000000]:
        bench, cleanup = make_threads_bench(num_bytes)
        runner.bench_time_func(f"pingpong_threads_{num_bytes}b", bench)
        cleanup()

        bench, cleanup = make_mp_bench(num_bytes)
        runner.bench_time_func(f"pingpong_multiprocess_{num_bytes}b", bench)
        cleanup()

        bench, cleanup = make_subinterp_bench(num_bytes)
        runner.bench_time_func(f"pingpong_subinterp_{num_bytes}b", bench)
        cleanup()


if __name__ == "__main__":
    main()
