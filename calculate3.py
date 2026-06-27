import multiprocessing as mp
from dataclasses import dataclass

BATCH_SIZE = 1_000_000
MAX_WORKERS = 10
DONE = None


@dataclass
class Station:
    name: str
    temperature: float


@dataclass
class StationAggData:
    minimum: float
    maximum: float
    current_sum: float
    count: int


Result = dict[str, StationAggData]


def validate_measurement_row(row: str) -> tuple[str, float]:
    name, temperature = row.split(";")

    # if not isinstance(name, str):
    #     raise ValueError('station name is not string')
    #
    # try:
    #     temperature = float(temperature)
    # except ValueError:
    #     raise ValueError(f'temperature for station={name} is not correct {temperature=}') from None

    return str(name), float(temperature)


def put_measurements(que: mp.Queue, filename: str) -> None:
    with open(filename, mode='r') as f:
        batch = []
        count = 0
        for row in f:
            name, temperature = validate_measurement_row(row)
            batch.append(Station(name=name, temperature=temperature))
            count += 1

            if count == BATCH_SIZE:
                que.put_nowait(batch)
                batch = []
                count = 0

        if batch:
            que.put_nowait(batch)

    for _ in range(MAX_WORKERS):
        que.put_nowait(DONE)

    return


def calc_measurement_batch(stations: list[Station]):
    result: Result = {}
    for station in stations:
        if station.name not in result:
            result[station.name] = StationAggData(
                minimum=station.temperature,
                maximum=station.temperature,
                current_sum=station.temperature,
                count=1
            )
            continue

        calc_data = result[station.name]
        if station.temperature < calc_data.minimum:
            result[station.name].minimum = station.temperature
        if station.temperature > calc_data.maximum:
            result[station.name].maximum = station.temperature

        result[station.name].current_sum += station.temperature
        result[station.name].count += 1

    return result


def calc_measurement(que_in: mp.Queue[list[Station]], que_out: mp.Queue[Result]):
    while True:
        stations = que_in.get()
        if stations is DONE:
            break

        result = calc_measurement_batch(stations)
        que_out.put_nowait(result)


def print_result(result: Result) -> None:
    print("{", end="")
    for station_name, result_data in sorted(result.items()):
        average = result_data.current_sum / result_data.count if result_data.count != 0 else 0
        print(f"{station_name}={result_data.minimum:.1f}/{average:.1f}/{result_data.maximum:.1f}", end=", ")

    print("\b\b} ")


def process_measurements(que_in: mp.Queue, que_out: mp.Queue):
    procs = []
    for worker in range(MAX_WORKERS):
        proc = mp.Process(target=calc_measurement, args=(que_in, que_out), name=f'worker-{worker + 1}')
        procs.append(proc)
        proc.start()

    for proc in procs:
        proc.join()

    que_out.put_nowait(DONE)


def combine_measurements(que_out: mp.Queue[Result]) -> Result:
    result: Result = {}
    while True:
        batch_result = que_out.get()
        if batch_result is DONE:
            break

        for station_name, batch_agg_data in batch_result.items():
            if station_name not in result:
                result[station_name] = batch_agg_data
                continue

            curr_agg_data = result[station_name]
            if batch_agg_data.minimum < curr_agg_data.minimum:
                curr_agg_data.minimum = batch_agg_data.minimum
            if batch_agg_data.maximum > curr_agg_data.maximum:
                curr_agg_data.maximum = batch_agg_data.maximum

            curr_agg_data.current_sum += batch_agg_data.current_sum
            curr_agg_data.count += batch_agg_data.count

    return result


def main() -> int:
    que_in = mp.Queue(maxsize=50)
    put_measurements_proc = mp.Process(
        target=put_measurements, args=(que_in, "measurements_medium.txt"), name='put-measurements'
    )
    put_measurements_proc.start()

    que_out = mp.Queue(maxsize=50)
    process_measurements_proc = mp.Process(
        target=process_measurements, args=(que_in, que_out), name='process-measurements'
    )
    process_measurements_proc.start()

    result = combine_measurements(que_out)

    put_measurements_proc.join()
    process_measurements_proc.join()

    print_result(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
