import unittest


from influxpy.protocol import encode_line


class TestEncodeLine(unittest.TestCase):

    weather_fields = {"temperature": 8.0}
    station_tags = {"station": "A1"}
    ts = 1533390240607501568  # nanos
    xy_field = {"x": "y"}
    xy_tag = {"x": "y"}

    def test__one_field(self):
        result = encode_line("weather", {}, self.weather_fields).decode("utf-8")
        self.assertEqual("weather temperature=8.0", result)

    def test__one_tag_one_field(self):
        result = encode_line("weather", self.station_tags, self.weather_fields).decode("utf-8")
        self.assertEqual("weather,station=A1 temperature=8.0", result)

    def test__one_field_with_timestamp(self):
        result = encode_line("weather", {}, self.weather_fields, ts=self.ts).decode("utf-8")
        self.assertEqual("weather temperature=8.0 1533390240607501568", result)

    def test__tag_int_value(self):
        result = encode_line("m", {"t": 1}, self.xy_field).decode("utf-8")
        self.assertEqual('m,t=1 x="y"', result)

    def test__field_int_value(self):
        result = encode_line("m", {}, {"i": 3}).decode("utf-8")
        self.assertEqual("m i=3i", result)

    def test__field_bool_value_true(self):
        result = encode_line("m", {}, {"b": True}).decode("utf-8")
        self.assertEqual("m b=true", result)

    def test__field_bool_value_false(self):
        result = encode_line("m", {}, {"b": False}).decode("utf-8")
        self.assertEqual("m b=false", result)

    def test__escape_tags_key_and_val(self):
        result = encode_line("m", {"t t": "v,v", "u=u": "v,v"}, self.xy_field).decode("utf-8")
        self.assertEqual('m,t\\ t=v\\,v,u\\=u=v\\,v x="y"', result)

    def test__escape_field_keys(self):
        result = encode_line("m", {}, {"t t": "v,v", "u=u": "v,v"}).decode("utf-8")
        self.assertEqual('m t\\ t="v,v",u\\=u="v,v"', result)

    def test__escape_field_keys_awkward(self):
        result = encode_line("m", {}, {"t\\,t": "val"}).decode("utf-8")
        self.assertEqual('m t\\\\\\,t="val"', result)

    def test__empty_fields__fail(self):
        with self.assertRaisesRegex(ValueError, "need at least one field value"):
            encode_line("weather", {}, {})

    def test__ts_not_int__fail(self):
        with self.assertRaisesRegex(ValueError, "ts not an integer"):
            encode_line("m", self.xy_tag, self.xy_field, ts=5.0)

    def test__empty_measurement__fail(self):
        with self.assertRaisesRegex(ValueError, "none or empty measurement"):
            encode_line("", self.xy_tag, self.xy_field)
