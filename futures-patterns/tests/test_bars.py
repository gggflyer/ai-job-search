import os
import sys
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from analysis.bars import Bar, label_bars, range_label, close_rel_label, resample  # noqa: E402
from analysis.patterns import next_bar_outcome, build_setups, conditional_table  # noqa: E402
from analysis.intrabar import build_path_bars  # noqa: E402

T0 = datetime(2026, 1, 5, 9, 30)


def mk(i, o, h, l, c):
    return Bar(T0 + timedelta(minutes=5 * i), o, h, l, c, 1)


class RangeLabels(unittest.TestCase):
    def test_four_way(self):
        p = mk(0, 10, 12, 8, 11)
        self.assertEqual(range_label(mk(1, 11, 12, 8, 11), p), "I")   # ties are inside
        self.assertEqual(range_label(mk(1, 11, 11.5, 9, 11), p), "I")
        self.assertEqual(range_label(mk(1, 11, 13, 7, 11), p), "O")
        self.assertEqual(range_label(mk(1, 11, 13, 8, 11), p), "U")
        self.assertEqual(range_label(mk(1, 11, 12, 7, 11), p), "D")

    def test_close_rel(self):
        p = mk(0, 10, 12, 8, 11)
        self.assertEqual(close_rel_label(mk(1, 11, 13, 9, 12.25), p), "A")
        self.assertEqual(close_rel_label(mk(1, 11, 13, 9, 12), p), "W")   # tie is within
        self.assertEqual(close_rel_label(mk(1, 11, 13, 7, 7.5), p), "B")

    def test_own_close_position(self):
        L = label_bars([mk(0, 10, 12, 8, 12), mk(1, 12, 12, 8, 8)], tick=0.25)
        self.assertTrue(L[0].closes_on_high)
        self.assertTrue(L[1].closes_on_low)
        self.assertTrue(L[1].opens_on_high)
        self.assertAlmostEqual(L[0].close_pos, 1.0)


class Outcomes(unittest.TestCase):
    def test_cross_and_hold(self):
        s = mk(0, 10, 12, 8, 11)
        o = next_bar_outcome(s, mk(1, 11, 13, 10, 12.5), tick=0.25)
        self.assertTrue(o.flags["cross_high"] and o.flags["close_above_high"])
        self.assertFalse(o.flags["cross_high_fail"])
        self.assertTrue(o.long_filled)
        self.assertAlmostEqual(o.long_pnl, (12.5 - 12.25) / 0.25)   # +1 tick
        self.assertAlmostEqual(o.long_mfe, 3.0)
        self.assertAlmostEqual(o.long_mae, -9.0)
        self.assertFalse(o.short_filled)

    def test_cross_and_fail(self):
        s = mk(0, 10, 12, 8, 11)
        o = next_bar_outcome(s, mk(1, 11, 12.5, 10, 11), tick=0.25)
        self.assertTrue(o.flags["cross_high_fail"])
        self.assertAlmostEqual(o.long_pnl, -5.0)

    def test_tie_is_not_a_cross_and_no_fill(self):
        s = mk(0, 10, 12, 8, 11)
        o = next_bar_outcome(s, mk(1, 11, 12, 9, 11.5), tick=0.25)
        self.assertFalse(o.flags["cross_high"])
        self.assertTrue(o.flags["inside"])
        self.assertFalse(o.long_filled)

    def test_no_lookahead_and_keys(self):
        bars = [mk(0, 10, 12, 8, 11), mk(1, 11, 11.5, 9, 10), mk(2, 10, 11, 9.5, 10.5), mk(3, 10.5, 13, 10, 12.75)]
        L = label_bars(bars, 0.25)
        setups = build_setups(L, lookback=2, key_kind="range", tick=0.25)
        # bars 1,2 are both inside -> key "I I", outcome measured on bar 3
        self.assertEqual([s.key for s in setups], ["I I"])
        self.assertTrue(setups[0].outcome.flags["close_above_high"])
        base, rows = conditional_table(setups)
        self.assertEqual(base.n, 1)

    def test_same_day_only_skips_session_break(self):
        b0 = mk(0, 10, 12, 8, 11)
        b1 = mk(1, 11, 11.5, 9, 10)
        b2 = Bar(b1.ts + timedelta(days=1), 10, 11, 9.5, 10.5, 1)
        L = label_bars([b0, b1, b2], 0.25)
        self.assertEqual(build_setups(L, 1, "range", 0.25), [])
        self.assertEqual(len(build_setups(L, 1, "range", 0.25, same_day_only=False)), 1)


class Resample(unittest.TestCase):
    def test_five_minutes(self):
        m = [Bar(T0 + timedelta(minutes=i), 10 + i, 11 + i, 9 + i, 10.5 + i, 1) for i in range(7)]
        r = resample(m, 5)
        self.assertEqual(len(r), 2)
        self.assertEqual((r[0].open, r[0].high, r[0].low, r[0].close, r[0].volume), (10, 15, 9, 14.5, 5))
        self.assertEqual(r[1].ts, T0 + timedelta(minutes=5))

    def test_path(self):
        # minute 0 makes the high, minute 3 makes the low -> high first, open is high
        m = [Bar(T0, 10, 12, 10, 11, 1), Bar(T0 + timedelta(minutes=1), 11, 11, 9, 9, 1),
             Bar(T0 + timedelta(minutes=2), 9, 10, 9, 10, 1), Bar(T0 + timedelta(minutes=3), 10, 10, 7, 8, 1),
             Bar(T0 + timedelta(minutes=4), 8, 9, 8, 8.5, 1)]
        pb = build_path_bars(m, 5, 0.25)[0]
        self.assertTrue(pb.high_first)
        self.assertFalse(pb.open_is_high)   # open 10, high 12
        self.assertEqual(pb.first_sub_dir, "+")
        self.assertEqual(pb.bar.close, 8.5)


if __name__ == "__main__":
    unittest.main()


class Conversions(unittest.TestCase):
    def test_utc_to_eastern_and_close_shift(self):
        from analysis.bars import convert_tz, shift_close_to_open
        # NinjaTrader style: close-stamped UTC. January is EST (UTC-5): 14:31 UTC -> 09:30 ET open time
        b = [Bar(datetime(2026, 1, 5, 14, 31), 1, 2, 0, 1, 1)]
        out = convert_tz(shift_close_to_open(b, 1), "UTC", "America/New_York")
        self.assertEqual(out[0].ts, datetime(2026, 1, 5, 9, 30))
        # July is EDT (UTC-4): 13:31 UTC -> 09:30 ET
        b = [Bar(datetime(2026, 7, 6, 13, 31), 1, 2, 0, 1, 1)]
        out = convert_tz(shift_close_to_open(b, 1), "UTC", "America/New_York")
        self.assertEqual(out[0].ts, datetime(2026, 7, 6, 9, 30))
