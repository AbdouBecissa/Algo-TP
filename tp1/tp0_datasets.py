import argparse
import io
import os
import random
import re
import time
import zipfile

import requests

OUT_DIR = "datasets"
CACHE_DIR = os.path.join(OUT_DIR, "_cache")
HEADERS = {"User-Agent": "Mozilla/5.0"}

T5K_ZIP = "https://t5k.org/lists/small/millions/primes{n}.zip"
T5K_ZIP_MIRROR = "https://primes.utm.edu/lists/small/millions/primes{n}.zip"


def is_prime(n):
    if n < 2:
        return False
    small = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    for p in small:
        if n % p == 0:
            return n == p
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in small:
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def http_get(url, retries=2, timeout=30):
    for i in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout)
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            print(f"  ! request failed {url} ({e}) - attempt {i + 1}/{retries}")
            time.sleep(1)
    return None


def load_t5k_list(n):
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache = os.path.join(CACHE_DIR, f"primes{n}.txt")
    if os.path.exists(cache):
        with open(cache) as f:
            return [int(x) for x in f.read().split()]
    print(f"Downloading t5k.org list primes{n}.zip ...")
    r = http_get(T5K_ZIP.format(n=n), timeout=120) or http_get(T5K_ZIP_MIRROR.format(n=n), timeout=120)
    if r is None:
        raise SystemExit(f"Could not download primes{n}.zip")
    z = zipfile.ZipFile(io.BytesIO(r.content))
    text = z.read(z.namelist()[0]).decode("ascii", "ignore")
    nums = [int(x) for x in re.findall(r"\b\d+\b", text.split("\n", 1)[1])]
    with open(cache, "w") as f:
        f.write("\n".join(map(str, nums)))
    print(f"  -> {len(nums)} primes imported")
    return nums


def generate_primes_with_digits(digits, count, rng):
    lo, hi = 10 ** (digits - 1), 10 ** digits - 1
    found = set()
    while len(found) < count:
        n = rng.randint(lo, hi) | 1
        if n <= hi and is_prime(n):
            found.add(n)
    return sorted(found)


def primes_with_digits(pool, digits, count, rng):
    if digits <= 8:
        sub = [p for p in pool if len(str(p)) == digits]
        return sorted(rng.sample(sub, count))
    if digits == 9:
        return sorted(rng.sample(load_t5k_list(10), count))
    print(f"  no downloadable list for {digits} digits: generating {count} Miller-Rabin verified primes")
    return generate_primes_with_digits(digits, count, rng)


def write_dataset(name, numbers):
    os.makedirs(OUT_DIR, exist_ok=True)
    valid = [n for n in numbers if is_prime(n)]
    if len(valid) != len(numbers):
        print(f"  ! {len(numbers) - len(valid)} non-prime numbers removed from {name}")
    path = os.path.join(OUT_DIR, f"{name}.txt")
    with open(path, "w") as f:
        f.write("\n".join(map(str, valid)) + "\n")
    print(f"[OK] {path} ({len(valid)} numbers)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    rng = random.Random(args.seed)

    pool = load_t5k_list(1)

    write_dataset("Random100", sorted(rng.sample(pool, 100)))
    write_dataset("Random1000", sorted(rng.sample(pool, 1000)))

    inter = [p for p in pool if 1000 <= p <= 1_000_000]
    write_dataset("Test-1", sorted(rng.sample(inter, 100)))

    t2 = []
    for d in range(3, 11):
        print(f"Test-2: {d} digits")
        t2 += primes_with_digits(pool, d, 10, rng)
    write_dataset("Test-2", t2)

    t3 = []
    for d in (3, 6, 9, 12):
        print(f"Test-3: {d} digits")
        t3 += primes_with_digits(pool, d, 10, rng)
    write_dataset("Test-3", t3)


if __name__ == "__main__":
    main()