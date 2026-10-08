from __future__ import annotations

import importlib.util
import tempfile
import unittest
from datetime import date
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "build_resource_rows.py"
SPEC = importlib.util.spec_from_file_location("build_resource_rows", SCRIPT)
assert SPEC and SPEC.loader
ROWS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ROWS)


def build(csv_rows, **overrides):
    options = {
        "year": 2026,
        "month": 5,
        "holidays": {date(2026, 5, 5): "휴일"},
        "people_filter": set(),
        "columns": dict(ROWS.DEFAULT_COLUMNS),
        "location_map": dict(ROWS.DEFAULT_LOCATION_MAP),
        "customer_hints": [],
        "location_shift": "next-business-day",
        "data_start_row": 3,
        "work_start": 9,
        "work_end": 18,
        "half_boundary": 13.5,
        "holiday_label": "휴일",
        "leave_label": "연차",
        "internal_label": "내근",
        "morning_half_label": "오전반차",
        "afternoon_half_label": "오후반차",
    }
    options.update(overrides)
    return ROWS.build_plan(csv_rows, **options)


def csv_row(work_date, location, summary="", note="", plan=""):
    return {
        "WorkDate": work_date,
        "SubmitterName": "Alex",
        "SubmitterEmail": "alex@example.com",
        "WorkLocation": location,
        "TodaySummary": summary,
        "TomorrowPlan": plan,
        "Note": note,
    }


class BuildResourceRowsTests(unittest.TestCase):
    def test_shifts_location_across_weekend_and_holiday(self):
        plan = build([csv_row("2026-05-04", "재택", "Monday work")])
        person = plan["people"][0]
        may_six = next(row for row in person["rows"] if row["date"] == "2026-05-06")

        self.assertEqual(may_six["kind"], "internal")
        self.assertEqual(may_six["source"]["attendance_from"], "2026-05-04")
        self.assertEqual(may_six["cells"][5], {"formula": '=IF(OR(D8="",E8=""),"",E8-D8)'})

    def test_customer_inference_is_opt_in_and_supports_aliases(self):
        rows = [csv_row("2026-05-07", "외근", "Workshop at Acme Korea")]
        without_hint = build(rows, location_shift="same-day")
        with_hint = build(
            rows,
            location_shift="same-day",
            customer_hints=[("Acme Korea", "Acme")],
        )
        first = next(row for row in without_hint["people"][0]["rows"] if row["date"] == "2026-05-07")
        second = next(row for row in with_hint["people"][0]["rows"] if row["date"] == "2026-05-07")

        self.assertEqual(first["cells"][6], "")
        self.assertEqual(second["cells"][6], "Acme")

    def test_detects_half_day_from_same_day_summary(self):
        plan = build(
            [csv_row("2026-05-11", "", "오전반차 후 문서 작업")],
            location_shift="next-business-day",
        )
        rows = [row for row in plan["people"][0]["rows"] if row["date"] == "2026-05-11"]

        self.assertEqual([row["kind"] for row in rows], ["half_day", "summary_only"])
        self.assertEqual(rows[0]["cells"][3:5], [9, 13.5])
        self.assertEqual(rows[1]["cells"][5], {"formula": '=IF(OR(D14="",E14=""),"",E14-D14)'})

    def test_note_and_summary_half_day_stay_on_work_date(self):
        plan = build([csv_row("2026-05-11", "재택", "오전반차 후 문서 작업", note="오전반차")])
        halves = [row for row in plan["people"][0]["rows"] if row["kind"] == "half_day"]

        self.assertEqual([row["date"] for row in halves], ["2026-05-11"])

    def test_tomorrow_half_day_shifts_across_holiday_in_same_day_location_mode(self):
        plan = build(
            [csv_row("2026-05-04", "재택", "Planning", plan="오후반차")],
            location_shift="same-day",
        )
        halves = [row for row in plan["people"][0]["rows"] if row["kind"] == "half_day"]

        self.assertEqual([row["date"] for row in halves], ["2026-05-06"])
        self.assertEqual(halves[0]["cells"][3:5], [13.5, 18])

    def test_conflicting_half_days_require_review(self):
        plan = build([csv_row("2026-05-11", "재택", "오전반차", note="오후반차")])
        person = plan["people"][0]

        self.assertFalse(any(row["kind"] == "half_day" for row in person["rows"]))
        self.assertTrue(any("Conflicting" in warning for warning in person["warnings"]))

    def test_excludes_people_without_target_month_records(self):
        plan = build([csv_row("2026-01-12", "재택", "January only")])

        self.assertEqual(plan["people"], [])

    def test_keeps_cross_month_location_and_tomorrow_plan(self):
        plan = build([csv_row("2026-04-30", "재택", plan="오전반차")], holidays={})
        first_day = [row for row in plan["people"][0]["rows"] if row["date"] == "2026-05-01"]

        self.assertEqual([row["kind"] for row in first_day], ["half_day", "internal"])
        self.assertEqual(first_day[1]["source"]["attendance_from"], "2026-04-30")

    def test_formulas_follow_custom_start_row_after_half_day(self):
        plan = build(
            [csv_row("2026-05-01", "재택", "오전반차")],
            location_shift="same-day", data_start_row=7,
        )
        rows = plan["people"][0]["rows"]

        self.assertEqual(rows[0]["cells"][5], {"formula": '=IF(OR(D7="",E7=""),"",E7-D7)'})
        self.assertEqual(rows[1]["cells"][5], {"formula": '=IF(OR(D8="",E8=""),"",E8-D8)'})
        self.assertEqual(rows[2]["cells"][5], {"formula": '=IF(OR(D9="",E9=""),"",E9-D9)'})

    def test_uses_custom_holiday_label_and_red_content(self):
        plan = build([], holidays={date(2026, 5, 1): "Company holiday"})
        self.assertEqual(plan["people"], [])

        plan = build(
            [csv_row("2026-04-30", "재택")],
            holidays={date(2026, 5, 1): "Company holiday"},
        )
        row = plan["people"][0]["rows"][0]
        self.assertEqual(row["cells"][12], "Company holiday")
        self.assertTrue(row["red_m"])

    def test_load_rows_allows_optional_headers_to_be_absent(self):
        content = "WorkDate,SubmitterName,WorkLocation,TodaySummary\n2026-05-04,Alex,재택,Planning\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "daily.csv"
            path.write_text(content, encoding="utf-8")
            rows = ROWS.load_rows(path, dict(ROWS.DEFAULT_COLUMNS))

        self.assertEqual(rows[0]["SubmitterName"], "Alex")


if __name__ == "__main__":
    unittest.main()
