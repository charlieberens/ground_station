# Create a web socket server that sends "ok" every second
# It should be on port 5001

# Path: websocket.py

import asyncio
import websockets
import argparse
import serial  # pip install pyserial
import json
import numpy as np
import re
from queue import Queue

PORT = 5001

# Individual transmissions consist of:
# Transmission Number (byte)
# Packet Number (byte)
# Transmission Type (): LOG etc. followed by a space and then the data


logs = {}


def format_line(data):
    return f"[{data['transmission_number']}]\t({data['transmission_type']})\t{data['data']}"


def log(line, file="log.log", log_time=100, debug=False, overwrite=True):
    if debug:
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


async def serial_loop(ser, queues, args):
    current_packet = {}
    previous_time = 0
    i = 0
    while True:
        while ser.in_waiting:
            try:
                ser_bytes = ser.read_until(b"@")
                transmission_number = ser_bytes[0]
                packet_number = ser_bytes[1]
                packet_count = ser_bytes[2]

                data = ser_bytes[3:-1].decode("utf-8")
                if packet_number == 0:
                    transimission_type = data.split(" ")[0]
                    data = " ".join(data.split(" ")[1:])
                else:
                    transimission_type = None

                if transimission_type == "LOOP":
                    # previous_time = int(re.search(r"recentMicros=(\d+)", data).group(1))
                    previous_time = i
                    i += 1

                if packet_number == 0:
                    current_packet = {
                        "transmission_number": transmission_number,
                        "packet_count": packet_count,
                        "transimission_type": transimission_type,
                        "data": [data],
                        "packet_number": packet_number,
                        "time": previous_time,
                    }
                else:
                    if transmission_number != current_packet["transmission_number"]:
                        raise Exception("Dropped packet")
                    current_packet["data"].append(data)

                    if packet_number != current_packet["packet_number"] + 1:
                        raise Exception("Dropped packet")

                    current_packet["packet_number"] = packet_number

                if packet_number < packet_count - 1:
                    continue

                data = "".join(current_packet["data"])
                transimission_type = current_packet["transimission_type"]
                transmission_number = current_packet["transmission_number"]
                time = current_packet["time"]

                log(data, file=args.log, debug=args.debug, overwrite=args.overwrite)
                for queue in queues:
                    queue.put(
                        {
                            "transmission_number": transmission_number,
                            "transmission_type": transimission_type,
                            "data": data,
                            "time": time,
                        }
                    )
            except IndexError:
                pass
            except Exception as e:
                print(e)
        await asyncio.sleep(0.01)


async def print_loop(queue):
    while True:
        while not queue.empty():
            data = queue.get()
            print(format_line(data))
        await asyncio.sleep(0.01)


def extract_imu_data(data, time):
    sections = data.split("\t")

    output = []

    for section in sections:
        name, value = section.split("=")
        output.append({"source": name, "time": time, "value": float(value)})

    return output


TRANSMITABLES = {
    "LOG": lambda x, t: {
        "time": t,
        "value": x,
        "source": "LOG",
    },
    "IMU": extract_imu_data,
}


def process_websocket_data(data):
    if data["transmission_type"] not in TRANSMITABLES:
        return []
    return TRANSMITABLES[data["transmission_type"]](data["data"], data["time"])


async def websocket_loop(websocket, path, queue):
    while True:
        try:
            while not queue.empty():
                data = queue.get()
                data = process_websocket_data(data)

                if data:
                    await websocket.send(json.dumps(data))
        except Exception as e:
            print(e)
        await asyncio.sleep(0.001)


def main():
    parser = argparse.ArgumentParser(description="Serial port reader")
    parser.add_argument("port", help="Serial port")
    parser.add_argument("--log", help="Name of log file w/ extension")
    parser.add_argument("--overwrite", help="Overwrite log file", default=True)
    parser.add_argument(
        "--baudrate", help="Baudrate", default=115200, type=int, required=False
    )
    parser.add_argument(
        "--test", help="Baudrate", default=False, type=bool, required=False
    )
    parser.add_argument(
        "--debug",
        help="Prints serial data to stdout",
        default=False,
        type=bool,
        required=False,
    )
    args = parser.parse_args()

    print_queue = Queue()
    # TODO - Possibly different queues for different sockets
    websocket_queue = Queue()

    queues = [print_queue, websocket_queue]

    print(f"Opening serial port {args.port} at {args.baudrate} baudrate")
    ser = serial.Serial(args.port, args.baudrate)

    start_server = websockets.serve(
        lambda websocket, path: websocket_loop(websocket, path, websocket_queue),
        "localhost",
        PORT,
    )

    # Start both loops and run them concurrently
    asyncio.get_event_loop().run_until_complete(start_server)
    loop = asyncio.get_event_loop()
    loop.create_task(serial_loop(ser, queues, args))
    loop.create_task(print_loop(print_queue))
    loop.run_forever()


if __name__ == "__main__":
    main()
