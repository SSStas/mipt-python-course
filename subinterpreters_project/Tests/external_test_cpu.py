# Created by sobolevn
# https://gist.github.com/sobolevn/149a461c629f6e03aef3a772c7422b2e

# /// script
# requires-python = ">=3.14"
# dependencies = [
#   "pyperf",
#   "httpx",
# ]
# ///
#
# To run `Threading with NoGIL`, first build Python with:
# `./configure --with-pydebug --disable-gil && make`
# NOTE: Building with NoGIL will likely slow down other options (multiprocessing and subinterpreters),
# since NoGIL is not zero-cost.

import os
from concurrent.futures import (
    ProcessPoolExecutor,
    ThreadPoolExecutor,
    InterpreterPoolExecutor,
)

import httpx
import pyperf

def worker_cpu(arg: tuple[int, int]):
    start, end = arg
    fact = 1
    for i in range(start, end + 1):
        fact *= i

def worker_io(arg: tuple[int, int]):
    start, end = arg
    with httpx.Client() as client:
        for i in range(start, end + 1):
            client.get(f'http://jsonplaceholder.typicode.com/posts/{i}')

# For CPU:
worker = worker_cpu
WORKLOADS = [(1, 10000), (10001, 20000), (20001, 30000), (30001, 40000)]
# For IO:
# worker = worker_io
# WORKLOADS = [(1, 5), (6, 10), (11, 15), (16, 20)]

CPUS = os.cpu_count() or len(WORKLOADS)

def bench_regular():
    for work in WORKLOADS:
        worker(work)

def bench_threading():
    with ThreadPoolExecutor(CPUS) as executor:
        list(executor.map(worker, WORKLOADS))

def bench_multiprocessing():
    with ProcessPoolExecutor(CPUS) as executor:
        list(executor.map(worker, WORKLOADS))

def bench_subinterpreters():
    with InterpreterPoolExecutor(CPUS) as executor:
        list(executor.map(worker, WORKLOADS))

def main():
    runner = pyperf.Runner()
    runner.bench_func('Regular', bench_regular)
    runner.bench_func('Threading', bench_threading)
    runner.bench_func('Multiprocessing', bench_multiprocessing)
    runner.bench_func('Subinterpreters', bench_subinterpreters)

if __name__ == '__main__':
    main()
