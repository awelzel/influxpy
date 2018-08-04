"""
Heavily based on handler.py from graypy.
"""
import logging
from logging.handlers import DatagramHandler, SysLogHandler
import os.path
import sys
import socket

from influxpy.protocol import encode_line

NANOSECONDS_PER_SECOND = 1000 * 1000 * 1000
SYSLOG_LEVELS = {
    logging.CRITICAL: SysLogHandler.LOG_CRIT,
    logging.ERROR: SysLogHandler.LOG_ERR,
    logging.WARNING: SysLogHandler.LOG_WARNING,
    logging.INFO: SysLogHandler.LOG_INFO,
    logging.DEBUG: SysLogHandler.LOG_DEBUG,
}


class UDPHandler(DatagramHandler):
    """
    Log messages to InfluxDB using UDP.

    :param host: The host of the InfluxDB server.
    :param port: The port of the InfluxDB server.
    :param measurement: The name of the "measurement" (table) in InfluxDB.
    :param debugging_fields: Send debug fields if true (the default).
    :param extra_fields: Send extra fields on the log record to InfluxDB
        if true (the default).
    :param localname: Use specified hostname as host tag instead
        of socket.gethostname()
    :param facility: Set facility tag to use, else some magic based
        on sys.argv[0] happens.
    :param sock: for unit testing
    """
    def __init__(self, host, port, measurement, debugging_fields=True,
                 extra_fields=True, localname=None, fqdn=False, facility=None,
                 sock=None):
        DatagramHandler.__init__(self, host, int(port))
        self.measurement = measurement
        self.debugging_fields = debugging_fields
        self.extra_fields = extra_fields
        self.fqdn = fqdn
        self.localname = localname
        self.facility = facility
        self.sock = sock

        # Do some magic based on sys.argv[0] to figure out some kind of
        # facility - it might be better to just let the user decide...
        if not self.facility:
            self.facility = os.path.basename(sys.argv[0])
            self.facility = self.facility.replace(".", "_").replace("-", "_")
            self.facility = self.facility.replace(" ", "_")
            self.facility = self.facility.strip("_").lower()
            if not self.facility:
                raise ValueError("facility magic failed")

    def makePickle(self, record):
        """
        Prepare all info and use influx.protocol.encode_line to create
        the message.
        """
        ts = int(record.created * NANOSECONDS_PER_SECOND)
        msg = record.getMessage()
        if self.localname:
            host = self.localname
        else:
            host = socket.getfqdn() if self.fqdn else socket.gethostname()

        tags = {
            "host": host,
            "level": SYSLOG_LEVELS.get(record.levelno, record.levelno),
            "level_name": logging.getLevelName(record.levelno),
            "facility": self.facility,
            "logger": record.name,
        }
        fields = {
            "message": msg,
        }

        # Use pre-formatted exception information in cases where the primary
        # exception information was removed, eg. for LogRecord serialization
        if record.exc_info and not record.exc_text:
            # format exception information if present
            formatter = logging._defaultFormatter
            record.exc_text = formatter.formatException(record.exc_info)
        if record.exc_text:
            fields["full_message"] = "\n".join([msg, record.exc_text])

        # Add debugging fields if enabled
        if self.debugging_fields:
            fields.update({
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName,
                "pid": record.process,
                "thread_name": record.threadName,
            })
            pn = getattr(record, "processName", None)
            if pn is not None:
                fields["process_name"] = pn

        if self.extra_fields:
            fields = add_extra_fields(fields, record)

        return encode_line(self.measurement, tags, fields, ts=ts)


def add_extra_fields(d, record):
    """
    Put extra key/values found in record.__dict__ into d.

    :param d: dict for values
    :param record: The log record.
    """
    # skip_list is used to filter additional fields in a log message.
    # It contains all attributes listed in
    # http://docs.python.org/library/logging.html#logrecord-attributes
    # plus exc_text, which is only found in the logging module source,
    # and id, which is prohibited by the GELF format.
    skip_list = (
        "args", "asctime", "created", "exc_info",  "exc_text", "filename",
        "funcName", "id", "levelname", "levelno", "lineno", "module",
        "msecs", "message", "msg", "name", "pathname", "process",
        "processName", "relativeCreated", "thread", "threadName"
    )
    for key, value in record.__dict__.items():
        if value is None:
            continue
        if key not in skip_list and not key.startswith("_"):
            d[key] = value
    return d
