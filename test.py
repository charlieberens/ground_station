"""
This script will send data to the frontend via a websocket as if it were websocket.py. The default port number is 5000.

Usage: python test.py --port <port_number>
"""

import argparse
import asyncio
import json
import math

import websockets
from queue import Queue

"""
This manages the websocket. Every time something is added to the queue (websocket_queue),
this function will send the data to the frontend.
"""


async def websocket_loop(websocket, path, queue):
    while True:
        try:
            while not queue.empty():
                data = queue.get()
                print("Sending Data")
                print(data)

                if data:
                    await websocket.send(json.dumps([data]))
        except Exception as e:
            print(e)
        await asyncio.sleep(0.001)


"""
This periodically adds data to the queue as if it were a ground station receiving data.
"""


async def data_generator(queue):
    t = 0
    while True:
        # Wait for .25 seconds
        await asyncio.sleep(0.25)
        queue.put(
            {
                "source": "accelx",
                "value": math.cos(t),
                "time": t,
            }
        )
        queue.put(
            {
                "source": "accely",
                "value": math.sin(t),
                "time": t,
            }
        )
        queue.put(
            {
                "source": "accelz",
                "value": t % 10,
                "time": t,
            }
        )
        t += 0.25


def main():
    parser = argparse.ArgumentParser(description="Dummy data generator")
    parser.add_argument("--port", help="Port number", default=5000, type=int)
    args = parser.parse_args()

    # Define the queue that is shared between the websocket and the data generator
    websocket_queue = Queue()

    # Websocket gobbledegook
    start_server = websockets.serve(
        lambda websocket, path: websocket_loop(websocket, path, websocket_queue),
        "localhost",
        args.port,
    )
    # Summon the websocket task
    asyncio.get_event_loop().run_until_complete(start_server)
    loop = asyncio.get_event_loop()
    # Summon the data generator task
    loop.create_task(data_generator(websocket_queue))
    loop.run_forever()


main()
