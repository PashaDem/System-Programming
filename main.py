import time
import time
from typing import Dict, List
from multiprocessing import Queue, Manager, Pool, current_process


def partition(data: List, chunk_size: int) -> List:
    for i in range(0, len(data), chunk_size):
        yield data[i : i + chunk_size]


def map_frequencies(chunk: List[str], queue: Queue) -> Dict[str, int]:
    counter = {}
    for line in chunk:
        word, _, count, _ = line.split("\t")
        if counter.get(word):
            counter[word] = counter[word] + int(count)
        else:
            counter[word] = int(count)

    queue.put(
        f"Another chunk was processed by {current_process().name} process. {time.time()}"
    )
    return counter


def merge_dictionaries(first: Dict[str, int], second: Dict[str, int]) -> Dict[str, int]:
    merged = first
    for key in second:
        if key in merged:
            merged[key] = merged[key] + second[key]
        else:
            merged[key] = second[key]
    return merged


def main(partition_size: int):
    with Manager() as manager:
        queue = manager.Queue()
        with open("googlebooks-eng-all-1gram-20120701-a", encoding="utf-8") as f:
            contents = f.readlines()
            with Pool(processes=8) as pool:
                params = []
                for chunk in partition(contents, partition_size):
                    params.append((chunk, queue))
                results = pool.starmap(map_frequencies, params)
        while not queue.empty():
            print(queue.get())


if __name__ == "__main__":
    main(partition_size=60000)
