"""Unit tests for the Hours-of-Service engine (no network: legs are given directly)."""
from datetime import datetime

from django.test import SimpleTestCase

from .hos_engine import (
    MAX_DRIVE_PER_WINDOW,
    STATUS_DRIVING,
    STATUS_OFF,
    Leg,
    build_daily_logs,
    simulate_trip,
)

START = datetime(2026, 1, 5, 8, 0)


def plan(miles_to_pickup, hours_to_pickup, miles_to_drop, hours_to_drop, cycle=0.0):
    return simulate_trip(
        START, cycle, "A", "B", "C",
        Leg("to pickup", "A", "B", miles_to_pickup, hours_to_pickup),
        Leg("to dropoff", "B", "C", miles_to_drop, hours_to_drop),
    )


class HOSEngineTests(SimpleTestCase):
    def test_short_trip_totals(self):
        r = plan(100, 2, 200, 4)
        self.assertEqual(r.total_distance_miles, 300.0)
        self.assertAlmostEqual(r.total_drive_hours, 6.0, places=2)
        # 6 h driving + 1 h pickup + 1 h drop-off on duty
        self.assertAlmostEqual(r.end_cycle_used, 8.0, places=2)

    def test_events_are_contiguous(self):
        r = plan(300, 5, 700, 12)
        for a, b in zip(r.events, r.events[1:]):
            self.assertEqual(a.end, b.start)

    def test_long_trip_takes_breaks_and_rests(self):
        r = plan(300, 5, 900, 16)
        remarks = " ".join(e.remark or "" for e in r.events).lower()
        self.assertTrue(any(e.status == STATUS_OFF and e.hours >= 10 - 1e-6 for e in r.events), "needs a 10 h rest")
        self.assertIn("break", remarks)

    def test_never_drives_more_than_11_hours_between_rests(self):
        r = plan(400, 7, 1100, 20)
        driving = 0.0
        for e in r.events:
            if e.status == STATUS_DRIVING:
                driving += e.hours
                self.assertLessEqual(driving, MAX_DRIVE_PER_WINDOW + 1e-6)
            elif e.status == STATUS_OFF and e.hours >= 10 - 1e-6:
                driving = 0.0

    def test_fuel_stop_after_1000_miles(self):
        r = plan(600, 10, 600, 10)
        self.assertTrue(any("fuel" in (e.remark or "").lower() for e in r.events))

    def test_daily_logs_cover_whole_days(self):
        r = plan(300, 5, 900, 16)
        logs = build_daily_logs(r.events, START)
        self.assertGreaterEqual(len(logs), 2)
        for day in logs:
            self.assertAlmostEqual(sum(day["totals"].values()), 24.0, places=1)


class PlanTripAPITests(SimpleTestCase):
    """The endpoint itself, with geocoding and routing stubbed out."""

    def _post(self, body):
        return self.client.post("/api/plan-trip/", body, content_type="application/json")

    def test_missing_fields_is_400(self):
        r = self._post({"current_location": "Dallas, TX"})
        self.assertEqual(r.status_code, 400)

    def test_non_text_location_is_400_not_500(self):
        r = self._post({"current_location": 123, "pickup_location": None, "dropoff_location": "Chicago"})
        self.assertEqual(r.status_code, 400)

    def test_cycle_out_of_range_is_400(self):
        r = self._post({"current_location": "A", "pickup_location": "B", "dropoff_location": "C", "current_cycle_used_hours": 80})
        self.assertEqual(r.status_code, 400)

    def test_full_plan(self):
        from unittest import mock
        legs = [{"distance": 330 * 1609.34, "duration": 5 * 3600}, {"distance": 800 * 1609.34, "duration": 13 * 3600}]
        with mock.patch("planner.views.geocode", side_effect=[(32.7, -96.8), (35.4, -97.5), (41.8, -87.6)]), \
             mock.patch("planner.views.osrm_route", return_value=({"type": "LineString", "coordinates": []}, legs)):
            r = self._post({"current_location": "Dallas, TX", "pickup_location": "Oklahoma City, OK",
                            "dropoff_location": "Chicago, IL", "current_cycle_used_hours": 12})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertAlmostEqual(data["route"]["total_distance_miles"], 1130.0, delta=1)
        self.assertGreaterEqual(len(data["daily_logs"]), 2)
        self.assertTrue(data["stops"])
