import sys
import math
import threading
import multiprocessing as mp
from typing import Callable

try:
    import pyperf
except ImportError:
    pyperf = None

try:
    from concurrent import interpreters
except ImportError:
    interpreters = None


def make_chunks(n_nodes: int, workers: int) -> list[tuple[int, int]]:
    base, rem = divmod(n_nodes, workers)
    chunks = list()
    start = 0
    for k in range(workers):
        size = base + (1 if k < rem else 0)
        end = start + size - 1
        chunks.append((start, end))
        start = end + 1
    return chunks


def f(x: float) -> float:
    return math.exp(-x * x) * math.sin(3.0 * x) * math.cos(7.0 * x)


def chunk_sum(a: float, h: float, n: int, i0: int, i1: int) -> float:
    s = 0.0
    for i in range(i0, i1 + 1):
        x = a + i * h
        fx = f(x)
        w = 1.0 if (i == 0 or i == n) else 2.0
        s += w * fx
    return s


# threads (noGIL speedup on 3.14t)

def thread_worker(a: float, h: float, n: int, i0: int, i1: int, out: list[float], idx: int) -> None:
    out[idx] = chunk_sum(a, h, n, i0, i1)


def make_threads_bench(workers: int, a: float, b: float, n: int, I_ref: float) -> Callable[[int], None]:
    def bench():
        h = (b - a) / n
        chunks = make_chunks(n + 1, workers)

        results = [0.0] * workers
        threads = list()

        for idx, (i0, i1) in enumerate(chunks):
            t = threading.Thread(target=thread_worker, args=(a, h, n, i0, i1, results, idx))
            t.start()
            threads.append(t)
        
        for t in threads:
            t.join()
        
        S = sum(results)
        I = (h / 2.0) * S

        assert abs(I - I_ref) < 1e-6, "Error: Incorrect answer"

    return bench


# multiprocessing

def mp_worker(a: float, h: float, n: int, i0: int, i1: int, q_out) -> None:
    q_out.put(chunk_sum(a, h, n, i0, i1))


def make_mp_bench(workers: int, a: float, b: float, n: int, I_ref: float) -> Callable[[int], None]:
    def bench():
        h = (b - a) / n
        chunks = make_chunks(n + 1, workers)

        ctx = mp.get_context("spawn")
        
        q_out = ctx.Queue()
        procs = list()

        for (i0, i1) in chunks:
            p = ctx.Process(target=mp_worker, args=(a, h, n, i0, i1, q_out))
            p.start()
            procs.append(p)

        S = 0.0

        for _ in range(workers):
            S += q_out.get()
        
        for p in procs:
            p.join()
        
        I = (h / 2.0) * S
        
        assert abs(I - I_ref) < 1e-6, "Error: Incorrect answer"

    return bench

# subinterpreters

def subinterp_worker(a: float, h: float, n: int, i0: int, i1: int, done_q) -> None:
    done_q.put(chunk_sum(a, h, n, i0, i1))


def make_subinterp_bench(workers: int, a: float, b: float, n: int, I_ref: float) -> Callable[[int], None]:
    def bench():
        h = (b - a) / n
        chunks = make_chunks(n + 1, workers)

        
        res = interpreters.create_queue()
        interps = list()
        threads = list()

        for (i0, i1) in chunks:
            interp = interpreters.create()
            t = interp.call_in_thread(subinterp_worker, a, h, n, i0, i1, res)
            interps.append(interp)
            threads.append(t)

        S = 0.0

        for _ in range(workers):
            S += res.get()
            
        I = (h / 2.0) * S

        for t in threads:
            t.join()

        for interp in interps:
            interp.close()

        assert abs(I - I_ref) < 1e-6, "Error: Incorrect answer"

    return bench


# check results
def compute_reference(a: float, b: float, n: int) -> float:
    h = (b - a) / n
    s = 0.0
    for i in range(0, n + 1):
        x = a + i * h
        w = 1.0 if (i == 0 or i == n) else 2.0
        s += w * f(x)
    return (h / 2.0) * s


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

    a = -1.0
    b = 1.0
    n = 2_000_000

    I_ref = compute_reference(a, b, n)

    for workers in range(1, 16 + 1):
        bench = make_threads_bench(workers, a, b, n, I_ref)
        runner.bench_func(f"integral_threads_w{workers}", bench)

        bench = make_mp_bench(workers, a, b, n, I_ref)
        runner.bench_func(f"integral_mp_w{workers}", bench)

        bench = make_subinterp_bench(workers, a, b, n, I_ref)
        runner.bench_func(f"integral_subinterp_w{workers}", bench)


if __name__ == "__main__":
    main()
