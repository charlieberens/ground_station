import serial # pip install pyserial
import argparse

def main():
    parser = argparse.ArgumentParser(description="Serial port reader")
    parser.add_argument("port", help="Serial port")
    parser.add_argument("--baudrate", help="Baudrate", default=9600, type=int, required=False)
    args = parser.parse_args()

    ser = serial.Serial(args.port, args.baudrate)
    while True:
        print(ser.readline().decode("utf-8").strip())

if __name__ == "__main__":
    main()