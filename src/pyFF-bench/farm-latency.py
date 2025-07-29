from fastflow import FFFarm, EOS
import random
import time
import hashlib
from multiprocessing import Value, Lock
import csv

# Shared total counter for sink
total_count = Value('i', 0)
lock = Lock()

def hash_workload(n):
    n = int(n)
    rounds = 800000
    value = str(n).encode()
    for _ in range(rounds):
        value = hashlib.sha256(value).digest()
    return value

class Source():
    def __init__(self, total_inputs):
        self.total_inputs = total_inputs
        self.counter = 0

    def svc(self, *arg):
        if self.counter >= self.total_inputs:
            return EOS
        self.counter += 1
        value = random.randint(1, 10000)
        timestamp = time.clock_gettime_ns(time.CLOCK_MONOTONIC)
        return [value, int(timestamp)]

class Worker():
    def __init__(self, worker_id):
        self.id = worker_id

    def svc(self, lis: list):
        value = lis[0]
        lis[0] = hash_workload(value)
        #time.sleep(0.5)
        return lis

'''
class Sink():
    def __init__(self):
        self.counter = 0
        self.total_latency_ns = 0

    def svc(self, lis: list):
        self.counter += 1
        source_timestamp = lis[1]
        current_time = time.clock_gettime_ns(time.CLOCK_MONOTONIC)
        latency = current_time - source_timestamp
        real = latency / 1_000_000
        print(f"[SINK] -> Latency {real} ms")
        #self.total_latency_ns += latency
'''

class Sink():
    def __init__(self, num_w, latency_log_file="./res/latency_finali_proc/latency_log"):
        self.counter = 0
        self.latency_log_file = f"{latency_log_file}_{num_w}.csv"
        self.latencies = []  # Store latencies in memory

    def svc(self, lis: list):
        self.counter += 1
        source_timestamp = lis[1]
        current_time = time.clock_gettime_ns(time.CLOCK_MONOTONIC)
        latency = current_time - source_timestamp

        # Store latency in the list
        self.latencies.append(latency)
    
    def svc_end(self):
        # Write all stored latencies to the file
        with open(self.latency_log_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["latency_ns"])  # Header
            for latency in self.latencies:
                writer.writerow([latency])


def run_benchmark(num_workers, total_inputs, use_subinterpreters=True):
    farm = FFFarm(use_subinterpreters)

    farm.add_emitter(Source(total_inputs))
    collector = Sink(num_workers)
    farm.add_workers([Worker(i) for i in range(num_workers)])
    farm.add_collector(collector)

    start = time.clock_gettime_ns(time.CLOCK_MONOTONIC)
    farm.run_and_wait_end()
    end = time.clock_gettime_ns(time.CLOCK_MONOTONIC)

    duration_sec = (end - start) / 1_000_000_000
    rate = total_inputs / duration_sec
    return rate, duration_sec


def run_tests(worker_counts, total_inputs, output_file, use_subinterpreters=True):
    for n in worker_counts:
        print(f"Testing with {n} worker(s)...")
        total_count.value = 0
        rate, duration = run_benchmark(n, total_inputs, use_subinterpreters)
        print(f"{n} worker(s): {rate:.2f} inputs/sec, Time: {duration:.4f} sec")

        # Write rate to original output file
        with open(output_file, "a", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([n, f"{rate:.2f}"])

        # Write time to separate file
        with open("res/fastflow_result_times_proc_ASH.csv", "a", newline="") as timefile:
            writer = csv.writer(timefile)
            writer.writerow([n, f"{duration:.4f}"])



if __name__ == "__main__":
    worker_counts = [1, 2, 3, 4, 6, 8, 10, 12, 14, 16, 20, 24, 28, 32]
    total_inputs = 1_000
    output_file = "res/fastflow_results.csv"
    run_tests(worker_counts, total_inputs, output_file, use_subinterpreters=False)
    print(f"\nBenchmark results written to {output_file}")
