import argparse
import logging

import influxpy


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--measurement", default="influxpy_logs")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8089)
    parser.add_argument("--facility", default=None)
    args = parser.parse_args()

    my_logger = logging.getLogger("test_logger")
    my_logger.setLevel(logging.DEBUG)

    handler = influxpy.UDPHandler(args.host, args.port, args.measurement,
                                  facility=args.facility)
    my_logger.addHandler(handler)

    my_logger.debug("Hello InfluxDB.")
    try:
        puff_the_magic_dragon()
    except NameError:
        my_logger.debug("No dragons here.", exc_info=1)

    # Include info about the stack
    my_logger.debug("Stack it!", stack_info=1)

    # Extra info through extra keyword argument
    my_logger.debug("Login successful.", extra={"username": "John"})

    my_logger.debug("UTF-8? \u270C")


if __name__ == "__main__":
    main()
