"""
Quick shot at the line protocol encoding of InfluxDB.
"""
import sys
if sys.version_info[0] == 3:
    int_types = (int,)
else:
    int_types = (int, long)


__all__ = ["encode_line"]


def encode_line(measurement, tags, fields, ts=None):
    """
    Given measurement, tags and fields create a valid influxdb line.

    https://docs.influxdata.com/influxdb/v1.6/write_protocols/line_protocol_tutorial/

    :param measurement: name of the measurement
    :param tags: Tags to be used, can be empty
    :param fields: Tags to be used. For no tags, set to None, False, {}, etc.
    :param ts: Set the timestamp explicitly as int in nanoseconds. If not
        provided the server will use its current time.
    """
    if not measurement:
        raise ValueError("none or empty measurement")
    if len(fields.keys()) < 1:
        raise ValueError("need at least one field value.")
    if ts is not None:
        try:
            int(str(ts + 1))
        except (ValueError, TypeError):
            raise ValueError("ts not an integer ({})".format(type(ts)))

    tags = tags or {}
    tags = _encode_tags(tags)
    fields = _encode_fields(fields)
    ts = " {:d}".format(ts) if ts else ""
    line = "{:s}{:s} {:s}{:s}".format(measurement, tags, fields, ts)
    return line.encode("utf-8")


def _escape_key(k):
    k = k.replace("\\", "\\\\")
    k = k.replace(",", "\\,")
    k = k.replace("=", "\\=")
    return k.replace(" ", "\\ ")


def _encode_tags(tags):
    if not tags:
        return ""
    escaped = []
    for k in sorted(tags):
        v = tags[k]
        v = _escape_key(str(tags[k]))
        k = _escape_key(str(k))
        escaped.append((k, v))
    return ",".join([""] + ["{:s}={:s}".format(k, v) for k, v in escaped])


def _escape_field_value(s):
    s = s.replace("\\", "\\\\")
    return s.replace('"', '\\"')


def _encode_fields(values):
    escaped = []
    for k in sorted(values):
        v = values[k]
        # bool first: isinstance(True, int) is True
        if isinstance(v, bool):
            v = "true" if v else "false"
        elif isinstance(v, int_types):
            v = "{:d}i".format(v)  # send as an actual integer
        elif isinstance(v, float):
            v = str(v)
        else:
            # Assume it is some sort of string
            v = '"{}"'.format(_escape_field_value(str(v)))
        escaped.append((_escape_key(k), v))

    return ",".join(["=".join([k, v]) for k, v in escaped])
