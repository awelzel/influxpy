import logging
import socket
import sys
import unittest
from unittest import mock

from influxpy import UDPHandler


class TestHandler(unittest.TestCase):
    """
    We mock UDP socket of the DatagramHandler and look at the sendto() call.
    """
    def setUp(self):
        self.logger = logging.getLogger("test_logger")
        for h in self.logger.handlers[:]:
            self.logger.removeHandler(h)

        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False
        self.sock_mock = mock.Mock(spec=socket.socket)
        self.handler = None

    def tearDown(self):
        if self.handler:
            self.handler.close()

    def test__log_defaults(self):
        self.handler = UDPHandler("127 0 0 1", -1, "test", sock=self.sock_mock)
        self.logger.addHandler(self.handler)
        self.logger.info("Hello")
        self.sock_mock.sendto.assert_called_once()
        data, to = self.sock_mock.sendto.call_args[0]
        data = data.decode("utf-8")
        self.assertRegex(data, "^test,")
        self.assertRegex(data, " [0-9]{15,}$")
        self.assertIn("level_name=INFO", data)
        self.assertIn('message="Hello"', data)
        self.assertIn('function="test__log_defaults"', data)

    def test__log_no_debugging_fields(self):
        self.handler = UDPHandler("127 0 0 1", -1, "xyz",
                                  debugging_fields=False,
                                  sock=self.sock_mock)
        self.logger.addHandler(self.handler)
        self.logger.info("A very long message.")
        self.sock_mock.sendto.assert_called_once()
        data, to = self.sock_mock.sendto.call_args[0]
        data = data.decode("utf-8")
        self.assertRegex(data, "^xyz,")
        self.assertRegex(data, " [0-9]{15,}$")
        self.assertNotIn("pid=", data)
        self.assertNotIn("function=", data)

    def test__log_utf8_message(self):
        self.handler = UDPHandler("127 0 0 1", -1, "xyz",
                                  sock=self.sock_mock)
        self.logger.addHandler(self.handler)
        self.logger.info("Yes: " + b"\xE2\x9C\x8C".decode("utf-8"))
        self.sock_mock.sendto.assert_called_once()
        data, to = self.sock_mock.sendto.call_args[0]
        data = data.decode("utf-8")
        self.assertIn('message="Yes: \u270C"', data)

    def test__localname(self):
        self.handler = UDPHandler("127 0 0 1", -1, "A",
                                  localname="test-host",
                                  sock=self.sock_mock)
        self.logger.addHandler(self.handler)
        self.logger.info("Aloha")
        self.sock_mock.sendto.assert_called_once()
        data, to = self.sock_mock.sendto.call_args[0]
        data = data.decode("utf-8")
        self.assertIn("host=test-host", data)

    def test__mocked_gethostbyname(self):
        self.handler = UDPHandler("127 0 0 1", -1, "A",
                                  sock=self.sock_mock)
        self.logger.addHandler(self.handler)
        with mock.patch("socket.gethostname") as m:
            m.return_value = "mock-host"
            self.logger.info("Aloha")
        data, to = self.sock_mock.sendto.call_args[0]
        data = data.decode("utf-8")
        self.assertIn("host=mock-host", data)

    def test__mocked_getfqdn(self):
        self.handler = UDPHandler("127 0 0 1", -1, "A",
                                  fqdn=True,
                                  sock=self.sock_mock)
        self.logger.addHandler(self.handler)
        with mock.patch("socket.getfqdn") as m:
            m.return_value = "fqdn-host"
            self.logger.info("Aloha")
        data, to = self.sock_mock.sendto.call_args[0]
        data = data.decode("utf-8")
        self.assertIn("host=fqdn-host", data)

    def test__extra_fields(self):
        self.handler = UDPHandler("127 0 0 1", -1, "xyz",
                                  sock=self.sock_mock)
        self.logger.addHandler(self.handler)
        extra = {
            "emails_processed": 10,
            "disk_utilization": 73.1,
        }
        self.logger.info("Processed 10 mails", extra=extra)
        data, to = self.sock_mock.sendto.call_args[0]
        data = data.decode("utf-8")
        self.assertIn('emails_processed=10i', data)
        self.assertIn('disk_utilization=73.1', data)

    def test__extra_fields_disabled(self):
        self.handler = UDPHandler("127 0 0 1", -1, "X",
                                  extra_fields=False,
                                  sock=self.sock_mock)
        self.logger.addHandler(self.handler)
        extra = {
            "emails_processed": 10,
            "disk_utilization": 73.1,
        }
        self.logger.info("Processed 10 mails", extra=extra)
        data, to = self.sock_mock.sendto.call_args[0]
        data = data.decode("utf-8")
        self.assertNotIn('emails_processed', data)
        self.assertNotIn('disk_utilization', data)

    def test__exception(self):
        self.handler = UDPHandler("127 0 0 1", -1, "X",
                                  sock=self.sock_mock)
        self.logger.addHandler(self.handler)

        try:
            puff_the_magic_dragon()
        except NameError:
            self.logger.exception("No dragons here.")
        data, to = self.sock_mock.sendto.call_args[0]
        data = data.decode("utf-8")
        self.assertIn('message="No dragons here."', data)
        full_msg = (
            'full_message="No dragons here.\n'
            'Traceback (most recent call last):\n'
        )
        self.assertIn(full_msg, data)

    def test__bad_facility_magic(self):
        argv0 = sys.argv[0]
        try:
            sys.argv[0] = "---"
            with self.assertRaisesRegex(ValueError, "facility magic failed"):
                UDPHandler("127 0 0 1", -1, "X")
        finally:
            sys.argv[0] = argv0
