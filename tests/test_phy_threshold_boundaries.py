"""Regression checks for the declared conservative equality policy."""
import math
import unittest
from uppaal_mcp.phy.alpha import classify_sample

CASES = [
    ("SINR_c", "SINRClass", 0.0, ("OUTAGE", "OUTAGE", "LOW")),
    ("SINR_c", "SINRClass", 10.0, ("LOW", "LOW", "OK")),
    ("SINR_c", "SINRClass", 25.0, ("OK", "OK", "HIGH")),
    ("Pd", "PdClass", 0.5, ("FAILED", "FAILED", "LOW")),
    ("Pd", "PdClass", 0.9, ("LOW", "LOW", "OK")),
    ("Rfa", "RfaClass", 0.05, ("OK", "HIGH", "HIGH")),
    ("Rfa", "RfaClass", 0.2, ("HIGH", "CRITICAL", "CRITICAL")),
    ("AoS_CTRL", "AoSClass", 10.0, ("FRESH", "EXPIRED", "EXPIRED")),
]

class ThresholdTests(unittest.TestCase):
    def test_all_threshold_neighbours(self):
        for key, result_key, threshold, expected in CASES:
            for value, category in zip((math.nextafter(threshold, -math.inf), threshold,
                                        math.nextafter(threshold, math.inf)), expected):
                with self.subTest(key=key, value=value):
                    self.assertEqual(classify_sample({key: value})[result_key], category)

    def test_custom_age_limit(self):
        for value, expected in [(6.999, "FRESH"), (7, "EXPIRED"), (7.001, "EXPIRED")]:
            self.assertEqual(classify_sample({"AoS_CTRL": value}, {"AoS_max": 7})["AoSClass"], expected)

    def test_interval_interiors(self):
        for key, result_key, values in [
            ("SINR_c", "SINRClass", [(-1,"OUTAGE"),(5,"LOW"),(20,"OK"),(30,"HIGH")]),
            ("Pd", "PdClass", [(0.2,"FAILED"),(0.7,"LOW"),(0.99,"OK")]),
            ("Rfa", "RfaClass", [(0.01,"OK"),(0.1,"HIGH"),(0.3,"CRITICAL")]),
            ("AoS_CTRL", "AoSClass", [(0,"FRESH"),(11,"EXPIRED")]),
        ]:
            for value, expected in values:
                with self.subTest(key=key, value=value):
                    self.assertEqual(classify_sample({key:value})[result_key], expected)
