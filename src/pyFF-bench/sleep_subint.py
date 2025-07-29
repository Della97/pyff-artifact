from fastflow import FFFarm, EOS
import random
import time
from multiprocessing import Value, Lock
import csv

# Shared total counter for sink
total_count = Value('i', 0)
lock = Lock()

def right_rotate(value, amount):
    return ((value >> amount) | (value << (32 - amount))) & 0xFFFFFFFF

def sha256(message):
    # SHA-256 constants (first 32 bits of the fractional parts of the cube roots of the first 64 primes)
    k = [
        0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
        0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
        0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
        0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
        0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
        0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
        0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
        0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
        0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
        0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
        0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3,
        0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
        0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5,
        0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
        0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
        0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
    ]

    # Initial hash values
    h = [
        0x6a09e667, 0xbb67ae85,
        0x3c6ef372, 0xa54ff53a,
        0x510e527f, 0x9b05688c,
        0x1f83d9ab, 0x5be0cd19,
    ]

    # Pre-processing
    message = bytearray(message, 'utf-8')
    orig_len_in_bits = (8 * len(message)) & 0xffffffffffffffff
    message.append(0x80)

    while (len(message) * 8 + 64) % 512 != 0:
        message.append(0)

    message += orig_len_in_bits.to_bytes(8, byteorder='big')

    # Process the message in successive 512-bit chunks
    for chunk_start in range(0, len(message), 64):
        chunk = message[chunk_start:chunk_start + 64]
        w = [int.from_bytes(chunk[i:i+4], 'big') for i in range(0, 64, 4)]
        for i in range(16, 64):
            s0 = right_rotate(w[i - 15], 7) ^ right_rotate(w[i - 15], 18) ^ (w[i - 15] >> 3)
            s1 = right_rotate(w[i - 2], 17) ^ right_rotate(w[i - 2], 19) ^ (w[i - 2] >> 10)
            w.append((w[i - 16] + s0 + w[i - 7] + s1) & 0xFFFFFFFF)

        a, b, c, d, e, f, g, h0 = h

        for i in range(64):
            s1 = right_rotate(e, 6) ^ right_rotate(e, 11) ^ right_rotate(e, 25)
            ch = (e & f) ^ ((~e) & g)
            temp1 = (h0 + s1 + ch + k[i] + w[i]) & 0xFFFFFFFF
            s0 = right_rotate(a, 2) ^ right_rotate(a, 13) ^ right_rotate(a, 22)
            maj = (a & b) ^ (a & c) ^ (b & c)
            temp2 = (s0 + maj) & 0xFFFFFFFF

            h0 = g
            g = f
            f = e
            e = (d + temp1) & 0xFFFFFFFF
            d = c
            c = b
            b = a
            a = (temp1 + temp2) & 0xFFFFFFFF

        h = [
            (h[0] + a) & 0xFFFFFFFF,
            (h[1] + b) & 0xFFFFFFFF,
            (h[2] + c) & 0xFFFFFFFF,
            (h[3] + d) & 0xFFFFFFFF,
            (h[4] + e) & 0xFFFFFFFF,
            (h[5] + f) & 0xFFFFFFFF,
            (h[6] + g) & 0xFFFFFFFF,
            (h[7] + h0) & 0xFFFFFFFF,
        ]

    return b''.join(x.to_bytes(4, 'big') for x in h)

def hash_workload(n):
    n = int(n)
    rounds = 1000
    value = str(n)
    for i in range(rounds):
        value = sha256(value).hex()
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
        #lis[0] = hash_workload(value)
        time.sleep(0.5)
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
    def __init__(self, num_w, latency_log_file="./results/latency/sleep_subint/latency_log_sleep_subint.csv"):
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
        with open("results/fastflow_result_times_subint.csv", "a", newline="") as timefile:
            writer = csv.writer(timefile)
            writer.writerow([n, f"{duration:.4f}"])



if __name__ == "__main__":
    worker_counts = [1, 2, 3, 4, 6, 8, 10, 12, 14, 16, 20, 24, 28, 32]
    total_inputs = 1_000
    output_file = "res/fastflow_results.csv"
    run_tests(worker_counts, total_inputs, output_file, use_subinterpreters=False)
    print(f"\nBenchmark results written to {output_file}")
