# ``influxpy``

[![Coverage Status](https://coveralls.io/repos/github/awelzel/influxpy/badge.svg?branch=master)](https://coveralls.io/github/awelzel/influxpy?branch=master) [![Build Status](https://travis-ci.org/awelzel/influxpy.svg?branch=master)](https://travis-ci.org/awelzel/influxpy)

# About
Python logging handler that sends messages to InfluxDB via UDP using
the line protocol. There is decidedly no support for the HTTP input.

The code was heavily inspired by and based on [graypy][1].

# Usage

## Example

    import logging
    import influxpy

    my_logger = logging.getLogger("test_logger")
    my_logger.setLevel(logging.DEBUG)

    handler = influxpy.UDPHandler("localhost", 8089, "influxpy_logs",
                                  global_tags={"app": "example"})
    my_logger.addHandler(handler)

    my_logger.debug("Hello InfluxDB.")


Tracebacks are added as full messages::

    try:
        puff_the_magic_dragon()
    except NameError:
        my_logger.debug("No dragons here.", exc_info=1)


## InfluxDB Configuration

The UDP Input for InfluxDB has to be enabled in order to make use of this
library.

    # influxdb.conf:
    ...
    [[udp]]
    enabled = true
    bind-address = ":8089"
    database = "udp"

Also take note of the [InfluxDB UDP documentation][2].


## Configuration parameters

``influxpy.UDPHandler``:

  * **host** - The host of the InfluxDB server.
  * **port** - The UDP port of the InfluxDB server.
  * **measurement** - The name of the measurement/table in InfluxDB.
  * **debugging_fields** -  Send debugging fields if set to True. Defaults is to not include debugging fields.
  * **extra_fields** - send extra fields on the log record to InfluxDB if true (the default).
  * **fqdn** - Use ``socket.getfqdn()`` instead of ``socket.gethostname()`` to set the source host.
  * **localname** - Use the specified hostname as source host.
  * **global_tags** - optional dict of tags to add to every message.


# Schema

## Tags

The following tags will be added to every message:

    host, level, level_name, logger

The ``host`` is set to ``socket.gethostname()``, but can be changed
by setting ``fqdn``, or overriding it completly by providing ``localname``.
``level`` is the syslog level mapped to this message. ``level_name`` is
the respective Python logging level name (``INFO``, ``ERROR``, etc.).
The ``logger`` tag is simply the name of the Python logger.

It is possible to pass ``global_tags`` and thereby configure a set of
static tags that are added to every message. For example, the following
will put ``datacenter=us-west`` and ``app=snakeoil`` as global tags.

    handler = influxpy.UDPHandler("127.0.0.1", 8089, "",
                                  global_tags={
                                      "datacenter": "us-west",
                                      "app": "snakeoil"})

## Fields

    message, full_message

The ``full_message`` field is added only to messages for which an exception
traceback is available. That is, when using ``logger.exception()``
or setting ``exec_info=1`` explicitly.

When ``debugging_fields`` is set to True, the following fields are added
additionally:

    file, function, line, pid, process_name, thread_name

When ``extra_fields`` is set to True, any extra fields on the ``LogRecord``
instance are sent to InfluxDB. Adding extra fields can be achieved by
passing the ``extra`` keyword argument to a logger call, or using
``logging.LoggerAdapter``. See the Python logging documentation for
more information.

    my_logger.debug("Login successful.", extra={"username": "John"})
    my_logger.info("It is warm.", extra={"temperature": 26.3})
    my_logger.warn("Disk Report.", extra={"disk_utilization": 73.4,
                                          "disk_free_space_mb": 63129})

This allows to conveniently add timeseries information that can be
visualized using Grafana.


# Using with Django

It should be easy to integrate ``influxpy`` with Django's logging settings.


# Credits:
  * [graypy][1] / Sever Banesiu


[1]: https://github.com/severb/graypy
[2]: https://docs.influxdata.com/influxdb/v1.6/supported_protocols/udp/
