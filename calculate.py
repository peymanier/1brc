from dataclasses import dataclass


@dataclass
class Station:
    name: str
    temperature: float


STATIONS: list[Station] = []


def validate_measurement_row(row: str) -> tuple[str, float]:
    name, temperature = row.split(";")
    if not isinstance(name, str):
        raise ValueError('station name is not string')

    try:
        temperature = float(temperature)
    except ValueError:
        raise ValueError(f'temperature for station={name} is not correct {temperature=}') from None

    return name, temperature


def read_measurements(filename: str):
    with open(filename, mode='r') as f:
        for row in f:
            name, temperature = validate_measurement_row(row)
            STATIONS.append(Station(name=name, temperature=temperature))


@dataclass
class StationAggData:
    minimum: float
    maximum: float
    current_sum: float
    count: int


def calc_measurements() -> dict[str, StationAggData]:
    result: dict[str, StationAggData] = dict()
    for station in STATIONS:
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
        elif station.temperature > calc_data.maximum:
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
    read_measurements("short_measurements.txt")
    result = calc_measurements()
    print_result(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
