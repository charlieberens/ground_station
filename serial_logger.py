# Reads data from a serial port, logs it to a file, and prints it on stdout
import asyncio
import argparse
import serial  # pip install pyserial
import json
import numpy as np

logs = {}


def log(line, file="log.log", log_time=100, overwrite=True):
    print(line)

    if file not in logs:
        logs[file] = []
        if overwrite:
            with open(file, "w") as f:
                f.write("")

    logs[file].append(line)

    if len(logs[file]) > log_time:
        with open(file, "a") as f:
            f.write("\n".join(logs[file]) + "\n")
        logs[file] = []


def close_logs():
    for file in logs:
        with open(file, "a") as f:
            f.write("\n".join(logs[file]))

    logs = {}


def main():
    parser = argparse.ArgumentParser(description="Serial port reader")
    parser.add_argument("port", help="Serial port")
    parser.add_argument("--log", help="Name of log file w/ extension")
    parser.add_argument("--overwrite", help="Overwrite log file", default=True)
    parser.add_argument(
        "--baudrate", help="Baudrate", default=9600, type=int, required=False
    )
    args = parser.parse_args()

    print(f"Opening serial port {args.port} at {args.baudrate} baudrate")
    ser = serial.Serial(args.port, args.baudrate)

    while True:
        line = ser.readline().decode("utf-8").strip()
        log(line, args.log, overwrite=args.overwrite)


if __name__ == "__main__":
    main()
