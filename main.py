"""ЛР №3: статистична обробка показників, зчитаних із CSV та INI."""

import argparse
import configparser
import csv
import json
import math
import sys
from datetime import datetime
from pathlib import Path

import stats_utils as su

BASE_DIR = Path(__file__).resolve().parent
PARAMETERS = ("temperature", "humidity", "pressure")
VALID_STATS = ("average", "min", "max", "median", "jumps")
DEFAULT_THRESHOLDS = {"temperature": 7.0, "humidity": 20.0, "pressure": 5000.0}


def read_csv(filename: Path) -> dict[str, dict[str, float]]:
    """Зчитує CSV у вкладені словники {датчик: {час: показ}}."""
    data: dict[str, dict[str, float]] = {name: {} for name in PARAMETERS}
    with filename.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        expected = ["timestamp", *PARAMETERS]
        if reader.fieldnames != expected:
            raise ValueError(f"Некоректний заголовок CSV. Очікується: {','.join(expected)}")
        previous: datetime | None = None
        for line, row in enumerate(reader, start=2):
            if None in row or any(row.get(key) is None for key in expected):
                raise ValueError(f"Рядок {line}: неправильна кількість полів")
            timestamp = row["timestamp"].strip()
            try:
                instant = datetime.fromisoformat(timestamp)
            except ValueError as exc:
                raise ValueError(f"Рядок {line}: некоректна часова мітка") from exc
            if previous is not None and instant <= previous:
                raise ValueError(f"Рядок {line}: часові мітки мають зростати")
            previous = instant
            for parameter in PARAMETERS:
                try:
                    value = float(row[parameter])
                except ValueError as exc:
                    raise ValueError(f"Рядок {line}: '{parameter}' не є числом") from exc
                if not math.isfinite(value):
                    raise ValueError(f"Рядок {line}: '{parameter}' має бути скінченним числом")
                data[parameter][timestamp] = value
    if not data["temperature"]:
        raise ValueError("Файл CSV не містить вимірювань")
    return data


def read_config(filename: Path) -> dict[str, list[str]]:
    """Повертає перелік потрібних характеристик для кожного розділу INI."""
    parser = configparser.ConfigParser(interpolation=None)
    with filename.open("r", encoding="utf-8-sig") as f:
        parser.read_file(f)
    if not parser.sections():
        raise ValueError("У конфігурації немає розділів датчиків")
    selected: dict[str, list[str]] = {}
    for parameter in parser.sections():
        if parameter not in PARAMETERS:
            raise ValueError(f"Невідомий датчик у конфігурації: {parameter}")
        if not parser.has_option(parameter, "stats"):
            raise ValueError(f"У розділі [{parameter}] відсутнє поле stats")
        requested = [s.strip().lower() for s in parser.get(parameter, "stats").split(",")]
        if not requested or any(s not in VALID_STATS for s in requested):
            raise ValueError(f"[{parameter}]: невідома або порожня характеристика")
        # При повторенні характеристик обчислюємо їх лише один раз.
        selected[parameter] = list(dict.fromkeys(requested))
    return selected


def analyze(
    data: dict[str, dict[str, float]],
    selected: dict[str, list[str]],
    thresholds: dict[str, float],
) -> dict[str, dict[str, float | list[str]]]:
    """Обчислює лише характеристики, які було вказано в INI."""
    operations = {
        "average": su.get_average,
        "min": su.get_min,
        "max": su.get_max,
        "median": su.get_median,
    }
    result: dict[str, dict[str, float | list[str]]] = {}
    for parameter, required in selected.items():
        timestamps = list(data[parameter])
        values = list(data[parameter].values())
        result[parameter] = {}
        for statistic in required:
            if statistic == "jumps":
                result[parameter][statistic] = su.detect_jumps(
                    values, timestamps, thresholds[parameter]
                )
            else:
                computed = operations[statistic](values)
                if computed is None:
                    raise ValueError("Недостатньо даних для обчислень")
                result[parameter][statistic] = computed
    return result


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Статистика мікроклімату з CSV")
    parser.add_argument("--data", type=Path, default=BASE_DIR / "data.csv", help="CSV файл")
    parser.add_argument("--config", type=Path, default=BASE_DIR / "config.ini", help="INI файл")
    parser.add_argument("--output", type=Path, default=BASE_DIR / "results.json", help="JSON файл")
    parser.add_argument("-t", "--temp-threshold", type=float, default=7.0, help="Поріг °C")
    parser.add_argument("-humi", "--humidity-threshold", type=float, default=20.0, help="Поріг %%")
    parser.add_argument("-p", "--pressure-threshold", type=float, default=5000.0, help="Поріг Па")
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()
    thresholds = dict(DEFAULT_THRESHOLDS)
    thresholds.update({
        "temperature": args.temp_threshold,
        "humidity": args.humidity_threshold,
        "pressure": args.pressure_threshold,
    })
    try:
        if any(not math.isfinite(v) or v < 0 for v in thresholds.values()):
            raise ValueError("Порогові значення повинні бути невід'ємними числами")
        data = read_csv(args.data)
        config = read_config(args.config)
        print(f"Зчитано вимірювань: {len(data['temperature'])}")
        for parameter in PARAMETERS:
            su.print_table(parameter, data[parameter])
        results = analyze(data, config, thresholds)
        for parameter, stats in results.items():
            su.print_statistics(parameter, stats)
        with args.output.open("w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
            f.write("\n")
        print(f"\nРезультати збережено у файлі: {args.output.name}")
        return 0
    except (OSError, ValueError, configparser.Error, csv.Error) as exc:
        print(f"Помилка: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
