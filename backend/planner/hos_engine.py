"""
Hours of Service (HOS) simulation engine.

Implements a simplified version of the FMCSA property-carrying driver
rules described in the "Interstate Truck Driver's Guide to Hours of
Service" (49 CFR Part 395), under the assumptions given for this
assessment:

  - Property-carrying driver
  - 70-hour / 8-day cycle (no 60/7 option)
  - No adverse driving conditions exception
  - Fuel stop at least once every 1,000 miles
  - 1 hour allotted for pickup and 1 hour for drop-off

Rules applied:
  - 11-hour driving limit within a 14-hour on-duty window
  - 30-minute break required after 8 cumulative hours of driving
  - 10 consecutive hours off duty required to reset the 11/14-hour clocks
  - 70-hour/8-day on-duty limit; a 34-consecutive-hour break resets it
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from typing import List, Optional

MAX_DRIVE_PER_WINDOW = 11.0
MAX_DUTY_WINDOW = 14.0
BREAK_AFTER_DRIVE = 8.0
SHORT_BREAK = 0.5
DAILY_REST = 10.0
CYCLE_LIMIT = 70.0
RESTART_HOURS = 34.0
FUEL_INTERVAL_MILES = 1000.0
FUEL_STOP_HOURS = 0.5
PICKUP_DROPOFF_HOURS = 1.0
AVG_SPEED_MPH_FALLBACK = 55.0

EPS = 1e-6

STATUS_OFF = "OFF"          # 1. Off Duty
STATUS_SLEEPER = "SB"       # 2. Sleeper Berth (not used by this simplified engine)
STATUS_DRIVING = "D"        # 3. Driving
STATUS_ON_DUTY = "ON"       # 4. On Duty (not driving)

STATUS_LABELS = {
    STATUS_OFF: "Off Duty",
    STATUS_SLEEPER: "Sleeper Berth",
    STATUS_DRIVING: "Driving",
    STATUS_ON_DUTY: "On Duty (Not Driving)",
}


@dataclass
class Leg:
    label: str
    from_label: str
    to_label: str
    distance_miles: float
    duration_hours: float


@dataclass
class Event:
    start: datetime
    end: datetime
    status: str
    remark: Optional[str] = None

    @property
    def hours(self) -> float:
        return (self.end - self.start).total_seconds() / 3600.0


@dataclass
class SimulationResult:
    events: List[Event] = field(default_factory=list)
    total_distance_miles: float = 0.0
    total_drive_hours: float = 0.0
    end_cycle_used: float = 0.0


class HOSSimulator:
    def __init__(self, start_datetime: datetime, cycle_used_hours: float):
        self.t = start_datetime
        self.cycle_used = cycle_used_hours
        self.drive_since_break = 0.0
        self.window_drive = 0.0
        self.window_duty = 0.0
        self.miles_since_fuel = 0.0
        self.total_distance = 0.0
        self.total_drive_hours = 0.0
        self.events: List[Event] = []

    def _push(self, status: str, hours: float, remark: Optional[str] = None):
        if hours <= EPS:
            return
        start = self.t
        end = self.t + timedelta(hours=hours)
        self.events.append(Event(start, end, status, remark))
        self.t = end

    def _reset_break(self):
        self.drive_since_break = 0.0

    def _reset_window(self):
        self.window_drive = 0.0
        self.window_duty = 0.0
        self.drive_since_break = 0.0

    def _take_short_break(self):
        self._push(STATUS_OFF, SHORT_BREAK, "30-minute break")
        self._reset_break()

    def _take_daily_rest(self):
        self._push(STATUS_OFF, DAILY_REST, "10-hour rest break")
        self._reset_window()

    def _take_restart(self):
        self._push(STATUS_OFF, RESTART_HOURS, "34-hour restart (70-hr cycle reset)")
        self._reset_window()
        self.cycle_used = 0.0

    def _ensure_capacity_for_stationary(self, hours: float):
        """Insert rest periods so a non-driving duty block of `hours` fits."""
        while True:
            if self.cycle_used + hours > CYCLE_LIMIT + EPS and self.cycle_used > EPS:
                self._take_restart()
                continue
            if self.window_duty + hours > MAX_DUTY_WINDOW + EPS and self.window_duty > EPS:
                self._take_daily_rest()
                continue
            break

    def add_stationary_duty(self, hours: float, remark: str):
        self._ensure_capacity_for_stationary(hours)
        self._push(STATUS_ON_DUTY, hours, remark)
        self.cycle_used += hours
        self.window_duty += hours

    def drive_leg(self, leg: Leg):
        remaining_hours = leg.duration_hours
        remaining_miles = leg.distance_miles
        avg_speed = (leg.distance_miles / leg.duration_hours) if leg.duration_hours > EPS else AVG_SPEED_MPH_FALLBACK

        first_chunk = True
        safety_counter = 0
        while remaining_hours > EPS:
            safety_counter += 1
            if safety_counter > 500:
                break

            if self.cycle_used >= CYCLE_LIMIT - EPS:
                self._take_restart()
                continue
            if self.drive_since_break >= BREAK_AFTER_DRIVE - EPS:
                self._take_short_break()
                continue
            if self.window_drive >= MAX_DRIVE_PER_WINDOW - EPS or self.window_duty >= MAX_DUTY_WINDOW - EPS:
                self._take_daily_rest()
                continue

            miles_to_fuel = FUEL_INTERVAL_MILES - self.miles_since_fuel
            hours_to_fuel = (miles_to_fuel / avg_speed) if avg_speed > EPS else float("inf")

            chunk = min(
                remaining_hours,
                BREAK_AFTER_DRIVE - self.drive_since_break,
                MAX_DRIVE_PER_WINDOW - self.window_drive,
                MAX_DUTY_WINDOW - self.window_duty,
                CYCLE_LIMIT - self.cycle_used,
                hours_to_fuel,
            )
            chunk = max(chunk, 0.0)
            if chunk <= EPS:
                self._take_daily_rest()
                continue

            remark = f"Depart {leg.from_label}" if first_chunk else None
            first_chunk = False

            self._push(STATUS_DRIVING, chunk, remark)
            chunk_miles = chunk * avg_speed

            self.drive_since_break += chunk
            self.window_drive += chunk
            self.window_duty += chunk
            self.cycle_used += chunk
            self.miles_since_fuel += chunk_miles
            self.total_distance += chunk_miles
            self.total_drive_hours += chunk

            remaining_hours -= chunk
            remaining_miles -= chunk_miles

            if self.miles_since_fuel >= FUEL_INTERVAL_MILES - EPS and remaining_hours > EPS:
                self.miles_since_fuel = 0.0
                self.add_stationary_duty(FUEL_STOP_HOURS, "Fuel stop")

        self._push(STATUS_OFF, 0, None)
        self.t = self.t  
        if self.events and self.events[-1].status == STATUS_DRIVING:
            pass

    def result(self) -> SimulationResult:
        return SimulationResult(
            events=self.events,
            total_distance_miles=round(self.total_distance, 1),
            total_drive_hours=round(self.total_drive_hours, 2),
            end_cycle_used=round(self.cycle_used, 2),
        )


def simulate_trip(
    start_datetime: datetime,
    cycle_used_hours: float,
    current_label: str,
    pickup_label: str,
    dropoff_label: str,
    leg_to_pickup: Leg,
    leg_to_dropoff: Leg,
) -> SimulationResult:
    sim = HOSSimulator(start_datetime, cycle_used_hours)

    sim.drive_leg(leg_to_pickup)
    sim.add_stationary_duty(PICKUP_DROPOFF_HOURS, f"Pickup at {pickup_label}")

    sim.drive_leg(leg_to_dropoff)
    sim.add_stationary_duty(PICKUP_DROPOFF_HOURS, f"Drop-off at {dropoff_label}")

    return sim.result()


def build_daily_logs(events: List[Event], start_datetime: datetime):
    if not events:
        return []

    first_day = start_datetime.date()
    last_day = events[-1].end.date()

    day_start = datetime.combine(first_day, datetime.min.time())
    if start_datetime > day_start:
        events = [Event(day_start, start_datetime, STATUS_OFF, "Start of shift")] + events

    logs = []
    day_cursor = first_day
    while day_cursor <= last_day:
        day_begin = datetime.combine(day_cursor, datetime.min.time())
        day_end = day_begin + timedelta(days=1)

        segments = []
        totals = {STATUS_OFF: 0.0, STATUS_SLEEPER: 0.0, STATUS_DRIVING: 0.0, STATUS_ON_DUTY: 0.0}

        for ev in events:
            seg_start = max(ev.start, day_begin)
            seg_end = min(ev.end, day_end)
            if seg_end <= seg_start:
                continue
            start_hr = (seg_start - day_begin).total_seconds() / 3600.0
            end_hr = (seg_end - day_begin).total_seconds() / 3600.0
            hrs = end_hr - start_hr
            totals[ev.status] += hrs
            segments.append({
                "start_hour": round(start_hr, 3),
                "end_hour": round(end_hr, 3),
                "status": ev.status,
                "status_label": STATUS_LABELS[ev.status],
                "remark": ev.remark,
                "remark_time": round(start_hr, 3) if ev.remark else None,
            })

        covered = sum(s["end_hour"] - s["start_hour"] for s in segments)
        if covered < 24 - 1e-3 and day_cursor == last_day:
            gap_start = covered
            segments.append({
                "start_hour": round(gap_start, 3),
                "end_hour": 24.0,
                "status": STATUS_OFF,
                "status_label": STATUS_LABELS[STATUS_OFF],
                "remark": None,
                "remark_time": None,
            })
            totals[STATUS_OFF] += (24 - gap_start)

        logs.append({
            "date": day_cursor.isoformat(),
            "segments": segments,
            "totals": {STATUS_LABELS[k]: round(v, 2) for k, v in totals.items()},
        })
        day_cursor += timedelta(days=1)

    return logs
