import concurrent.futures
from collections.abc import Iterator
from dataclasses import dataclass
from itertools import batched
from tqdm import tqdm


@dataclass
class Station:
    name: str
    temperature: float


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


def get_measurements(filename: str) -> Iterator[Station]:
    with open(filename, mode='r') as f:
        for row in f:
            name, temperature = validate_measurement_row(row)
            yield Station(name=name, temperature=temperature)


@dataclass
class StationAggData:
    minimum: float
    maximum: float
    current_sum: float
    count: int


BATCH_SIZE = 10_000_000


def calc_measurements(stations: Iterator[Station]) -> dict[str, StationAggData]:
    result: dict[str, StationAggData] = {}
    for station in tqdm(stations, total=BATCH_SIZE):
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


def print_result(result: dict[str, StationAggData]) -> None:
    print("{", end="")
    for station_name, result_data in sorted(result.items()):
        average = result_data.current_sum / result_data.count if result_data.count != 0 else 0
        print(f"{station_name}={result_data.minimum:.1f}/{average:.1f}/{result_data.maximum:.1f}", end=", ")

    print("\b\b} ")


def main() -> int:
    measurements = get_measurements("measurements.txt")

    result: dict[str, StationAggData] = {}
    with concurrent.futures.ProcessPoolExecutor() as exc:
        for stations in exc.map(calc_measurements, batched(measurements, BATCH_SIZE)):
            for station_name, batch_agg_data in stations.items():
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

    print_result(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
