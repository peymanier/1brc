import concurrent.futures
import os
import time
from dataclasses import dataclass

FILE_NAME = "measurements_medium.txt"


@dataclass
class ChunkRange:
    start: int
    end: int


@dataclass
class LocationTemperature:
    name: str
    measurement: float


@dataclass
class LocationAggregate:
    minimum: float
    maximum: float
    current_sum: float
    count: int


def get_chunks() -> list[ChunkRange]:
    file_size = os.path.getsize(FILE_NAME)
    chunk_size = file_size // os.cpu_count()

    def is_new_line(pos):
        if pos == 0:
            return True

        f.seek(pos - 1)
        return f.read(1) == b'\n'

    def next_line(pos):
        f.seek(pos)
        f.readline()
        return f.tell()

    chunks: list[ChunkRange] = []
    with open(FILE_NAME, 'rb') as f:
        chunk_start = 0
        while chunk_start < file_size:
            chunk_end = min(file_size, chunk_start + chunk_size)

            while not is_new_line(chunk_end):
                chunk_end -= 1

            if chunk_end == chunk_start:
                chunk_end = next_line(chunk_end)

            chunks.append(ChunkRange(start=chunk_start, end=chunk_end))
            chunk_start = chunk_end

    return chunks


def process_chunk(chunk: ChunkRange) -> dict:
    result: dict[str, LocationAggregate] = {}
    with open(FILE_NAME, 'rb') as f:
        chunk_start = chunk.start
        f.seek(chunk_start)
        for line in f:
            chunk_start += len(line)
            if chunk_start > chunk.end:
                break

            location, measurement = line.split(b';')
            location = location.decode()
            measurement = float(measurement)
            if location not in result:
                result[location] = LocationAggregate(
                    minimum=measurement,
                    maximum=measurement,
                    current_sum=measurement,
                    count=1
                )
            else:
                current_aggregate = result[location]
                if measurement > current_aggregate.maximum:
                    current_aggregate.maximum = measurement
                if measurement < current_aggregate.minimum:
                    current_aggregate.minimum = measurement

                current_aggregate.current_sum += measurement
                current_aggregate.count += 1

                result[location] = current_aggregate

    return result


def process_chunks(chunks):
    result: dict[str, LocationAggregate] = {}
    with concurrent.futures.ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        futures = [executor.submit(process_chunk, chunk) for chunk in chunks]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()

            for name, chunk_aggregate in result.items():
                current_aggregate = result[name]
                if chunk_aggregate.maximum > current_aggregate.maximum:
                    current_aggregate.maximum = chunk_aggregate.maximum
                if chunk_aggregate.minimum < current_aggregate.minimum:
                    current_aggregate.minimum = chunk_aggregate.minimum

                current_aggregate.current_sum += chunk_aggregate.current_sum
                current_aggregate.count += chunk_aggregate.count

                result[name] = current_aggregate

    return result


def print_result(result: dict[str, LocationAggregate]) -> None:
    print("{", end="")
    for name, location_aggregate in sorted(result.items()):
        average = location_aggregate.current_sum / location_aggregate.count if location_aggregate.count != 0 else 0
        print(f"{name}={location_aggregate.minimum:.1f}/{average:.1f}/{location_aggregate.maximum:.1f}", end=", ")

    print("\b\b} ")


def main():
    start_time = time.perf_counter()

    chunks = get_chunks()
    result = process_chunks(chunks)
    print_result(result)

    print(f'duration: {(time.perf_counter() - start_time):.2f} seconds')


if __name__ == "__main__":
    main()
