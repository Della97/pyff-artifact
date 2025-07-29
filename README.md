# Python Benchmarking Artifact

This repository contains benchmarking scripts and result logs for evaluating the performance of pure Python versus parallel implementations using either multiprocessing or **Python subinterpreters** (referred to as "subint"). The benchmarks include both CPU-bound tasks (e.g. SHA-256 hashing) and I/O-bound tasks (e.g. sleeping), and are designed to assess scalability, latency, and throughput across different parallelization strategies.

---

## Folder Overview

### `src/purepythonbench`

Contains the pure python implementation:
- `purepython_hash.py`: Performs repeated SHA-256 hashing.
- `purepython_sleep.py`: Runs sleep-based workloads to simulate I/O-bound delay.
- `results/`: Stores CSV files with benchmark results:
  - `results_purepy_hash.csv`
  - `results_purepy_sleep.csv`

### `src/pyFF-bench`

Contains parallel benchmarks using two concurrency models:
- **`*_proc.py`** scripts use multiprocessing (separate OS processes).
- **`*_subint.py`** scripts use subinterpreters (isolated Python interpreters in the same process).
- `farm-latency.py`: Main benchmark runner that executes tasks using multiple cores and logs latency and performance.
- `latency_log.csv`: Aggregated latency results from `farm-latency.py`.

The `results/` subdirectory includes:
- `latency/`: Contains detailed per-core latency logs, organized by method:
  - `hash_proc/`: Latency logs for multiprocessing runs.
  - `hash_subint/`: Latency logs for subinterpreter runs.
  - Each file represents a benchmark using a specific number of cores (e.g. `latency_log_ash_subint_8.csv` for 8-core subinterpreter run).

---

## Benchmark Summary

This benchmark suite evaluates:

- **Sequential Execution**:
  - Pure Python concurrency.
  
- **Parallel Execution**:
  - Using **multiprocessing** (`*_proc.py`)
  - Using **subinterpreters** (`*_subint.py`)

Each strategy is tested on both CPU-bound and I/O-bound workloads, with multiple core counts to observe scalability and overhead.

Metrics collected:
- Total execution time
- Latency per task/core

---

## Running the Benchmarks

### Requirements

- Python 3.9+ (for subinterpreter support via the `interpreters` module)
- FastFlow-Python

### Example Commands

```bash
# Run pure Python benchmarks
python src/purepythonbench/purepython_hash.py
python src/purepythonbench/purepython_sleep.py

# Run multiprocessing benchmarks
python src/pyFF-bench/hash_proc.py
python src/pyFF-bench/sleep_proc.py

# Run subinterpreter benchmarks
python src/pyFF-bench/hash_subint.py
python src/pyFF-bench/sleep_subint.py

# Run full latency experiment
python src/pyFF-bench/farm-latency.py
