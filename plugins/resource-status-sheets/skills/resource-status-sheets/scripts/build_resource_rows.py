#!/usr/bin/env python3
"""Build per-person monthly resource-sheet row plans from a DailyUpdates CSV."""

from __future__ import annotations

import argparse
import calendar
import csv
import html
import json
import re
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


MANAGED_COLUMNS = [
    "엔지니어",
    "월",
    "일",
    "시작시간",
    "종료시간",
    "근무시간",
    "고객명(실수요처)",
    "유지보수계약여부",
    "영업담당",
    "상주/비상주",
    "프로젝트코드",
    "프로젝트명",
    "업무내용",
]

DEFAULT_COLUMNS = {
    "WorkDate": "WorkDate",
    "SubmitterName": "SubmitterName",
    "SubmitterEmail": "SubmitterEmail",
    "WorkLocation": "WorkLocation",
    "TodaySummary": "TodaySummary",
    "TomorrowPlan": "TomorrowPlan",
    "Note": "Note",
}

REQUIRED_COLUMN_KEYS = {
    "WorkDate",
    "SubmitterName",
    "WorkLocation",
    "TodaySummary",
}

DEFAULT_LOCATION_MAP = {
    "출근": "internal",
    "재택": "internal",
    "내근": "internal",
    "외근": "external",
    "휴가": "leave",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", required=True, help="DailyUpdates CSV path")
    parser.add_argument("--year", required=True, type=int)
    parser.add_argument("--month", required=True, type=int)
    parser.add_argument(
        "--holiday",
        action="append",
        default=[],
        help="DATE or DATE=label; repeat for each non-working date",
    )
    parser.add_argument("--person", action="append", default=[], help="Limit output to a submitter name")
    parser.add_argument(
        "--column",
        action="append",
        default=[],
        metavar="LOGICAL=CSV_HEADER",
        help="Override a required CSV header; repeatable",
    )
    parser.add_argument(
        "--location-map",
        action="append",
        default=[],
        metavar="VALUE=KIND",
        help="Map a WorkLocation value to internal, external, or leave",
    )
    parser.add_argument(
        "--customer-hint",
        action="append",
        default=[],
        metavar="TEXT[=CANONICAL]",
        help="Infer an external-work customer only when this text occurs; repeatable",
    )
    parser.add_argument(
        "--work-location-shift",
        choices=("next-business-day", "same-day"),
        default="next-business-day",
        help="How each CSV row's WorkLocation maps to the sheet date",
    )
    parser.add_argument("--data-start-row", type=int, default=3)
    parser.add_argument("--work-start", type=float, default=9)
    parser.add_argument("--work-end", type=float, default=18)
    parser.add_argument("--half-boundary", type=float, default=13.5)
    parser.add_argument("--holiday-label", default="휴일")
    parser.add_argument("--leave-label", default="연차")
    parser.add_argument("--internal-label", default="내근")
    parser.add_argument("--morning-half-label", default="오전반차")
    parser.add_argument("--afternoon-half-label", default="오후반차")
    parser.add_argument("--output", help="Output JSON path; print to stdout when omitted")
    args = parser.parse_args()
    if not 1 <= args.month <= 12:
        parser.error("--month must be between 1 and 12")
    if args.data_start_row < 1:
        parser.error("--data-start-row must be positive")
    if not args.work_start < args.half_boundary < args.work_end:
        parser.error("expected --work-start < --half-boundary < --work-end")
    return args


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def parse_holidays(values: list[str], default_label: str = "휴일") -> dict[date, str]:
    holidays: dict[date, str] = {}
    for value in values:
        raw_date, separator, raw_label = value.partition("=")
        label = raw_label.strip() if separator else default_label
        holidays[parse_date(raw_date.strip())] = label or default_label
    return holidays


def parse_columns(values: list[str]) -> dict[str, str]:
    columns = dict(DEFAULT_COLUMNS)
    for value in values:
        logical, separator, header = value.partition("=")
        logical = logical.strip()
        header = header.strip()
        if not separator or logical not in columns or not header:
            allowed = ", ".join(DEFAULT_COLUMNS)
            raise SystemExit(f"Invalid --column {value!r}; expected one of [{allowed}]=CSV_HEADER")
        columns[logical] = header
    return columns


def parse_location_map(values: list[str]) -> dict[str, str]:
    locations = dict(DEFAULT_LOCATION_MAP)
    for value in values:
        label, separator, kind = value.partition("=")
        label = label.strip()
        kind = kind.strip()
        if not separator or not label or kind not in {"internal", "external", "leave"}:
            raise SystemExit(f"Invalid --location-map {value!r}; expected VALUE=internal|external|leave")
        locations[label] = kind
    return locations


def parse_customer_hints(values: list[str]) -> list[tuple[str, str]]:
    hints: list[tuple[str, str]] = []
    for value in values:
        needle, separator, canonical = value.partition("=")
        needle = needle.strip()
        canonical = canonical.strip() if separator else needle
        if not needle or not canonical:
            raise SystemExit(f"Invalid --customer-hint {value!r}")
        hints.append((needle, canonical))
    return hints


def clean_html(value: str) -> str:
    text = html.unescape(value or "")
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</p>\s*<p[^>]*>", "\n", text)
    text = re.sub(r"(?i)<li[^>]*>", "- ", text)
    text = re.sub(r"(?i)</li>", "\n", text)
    text = re.sub(r"<[^>]+>", " ", text)
    lines = []
    for line in text.splitlines():
        line = re.sub(r"[ \t]+", " ", line).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


def is_business_day(day: date, holidays: dict[date, str]) -> bool:
    return day.weekday() < 5 and day not in holidays


def next_business_day(day: date, holidays: dict[date, str]) -> date:
    cursor = day + timedelta(days=1)
    while not is_business_day(cursor, holidays):
        cursor += timedelta(days=1)
    return cursor


def month_days(year: int, month: int) -> list[date]:
    _, count = calendar.monthrange(year, month)
    return [date(year, month, day) for day in range(1, count + 1)]


def formula_for(spreadsheet_row: int) -> dict[str, str]:
    return {
        "formula": f'=IF(OR(D{spreadsheet_row}="",E{spreadsheet_row}=""),"",E{spreadsheet_row}-D{spreadsheet_row})'
    }


def row_obj(
    *,
    name: str,
    day: date,
    spreadsheet_row: int,
    kind: str,
    start: float | str = "",
    end: float | str = "",
    customer: str = "",
    maintenance: str = "",
    sales: str = "",
    residence: str = "",
    project_code: str = "",
    project_name: str = "",
    content: str = "",
    red_m: bool = False,
    source: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "date": day.isoformat(),
        "kind": kind,
        "red_m": red_m,
        "source": source or {},
        "cells": [
            name,
            day.month,
            day.day,
            start,
            end,
            formula_for(spreadsheet_row),
            customer,
            maintenance,
            sales,
            residence,
            project_code,
            project_name,
            content,
        ],
    }


def detect_half_day(
    attendance: dict[str, str] | None,
    summary: str,
    columns: dict[str, str],
    morning_label: str,
    afternoon_label: str,
) -> tuple[str | None, list[str]]:
    attendance_text = ""
    if attendance:
        attendance_text = "\n".join(
            clean_html(attendance.get(columns[key], "")) for key in ("Note", "TomorrowPlan")
        )
    compact = re.sub(r"\s+", "", "\n".join((attendance_text, summary)))
    morning = re.sub(r"\s+", "", morning_label) in compact
    afternoon = re.sub(r"\s+", "", afternoon_label) in compact
    if morning and afternoon:
        return None, ["Conflicting morning and afternoon half-day text; confirm the leave period."]
    if morning:
        return "morning", []
    if afternoon:
        return "afternoon", []
    warnings = []
    if "반차" in compact:
        warnings.append("Half-day text was found, but morning versus afternoon was not determined.")
    return None, warnings


def infer_customer(
    attendance: dict[str, str] | None,
    summary: str,
    columns: dict[str, str],
    hints: list[tuple[str, str]],
) -> str:
    text = summary
    if attendance:
        text = "\n".join(
            (
                summary,
                clean_html(attendance.get(columns["Note"], "")),
                clean_html(attendance.get(columns["TomorrowPlan"], "")),
            )
        )
    for needle, canonical in hints:
        if needle.casefold() in text.casefold():
            return canonical
    return ""


def load_rows(path: Path, columns: dict[str, str]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        required = {columns[key] for key in REQUIRED_COLUMN_KEYS}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise SystemExit(f"Missing required CSV columns: {', '.join(sorted(missing))}")
        return list(reader)


def build_plan(
    rows: list[dict[str, str]],
    *,
    year: int,
    month: int,
    holidays: dict[date, str],
    people_filter: set[str],
    columns: dict[str, str],
    location_map: dict[str, str],
    customer_hints: list[tuple[str, str]],
    location_shift: str,
    data_start_row: int,
    work_start: float,
    work_end: float,
    half_boundary: float,
    holiday_label: str,
    leave_label: str,
    internal_label: str,
    morning_half_label: str,
    afternoon_half_label: str,
) -> dict[str, Any]:
    people: set[str] = set()
    summaries: dict[str, dict[date, str]] = defaultdict(dict)
    emails: dict[str, str] = {}
    attendance: dict[str, dict[date, dict[str, str]]] = defaultdict(dict)
    leave_text: dict[str, dict[date, dict[str, str]]] = defaultdict(dict)
    warnings: list[str] = []

    for raw in rows:
        name = raw[columns["SubmitterName"]].strip()
        if not name or (people_filter and name not in people_filter):
            continue
        work_date = parse_date(raw[columns["WorkDate"]])
        plan_date = next_business_day(work_date, holidays)
        emails[name] = raw.get(columns["SubmitterEmail"], "")
        summaries[name][work_date] = clean_html(raw.get(columns["TodaySummary"], ""))
        target = work_date if location_shift == "same-day" else next_business_day(work_date, holidays)
        if target in attendance[name]:
            warnings.append(
                f"{name} {target.isoformat()} has multiple WorkLocation records; using the later CSV row."
            )
        attendance[name][target] = raw
        # Notes describe the current day; TomorrowPlan describes the next business
        # day. Neither inherits the independently configured WorkLocation shift.
        leave_text[name].setdefault(work_date, {})[columns["Note"]] = raw.get(columns["Note"], "")
        tomorrow_plan = raw.get(columns["TomorrowPlan"], "")
        if tomorrow_plan:
            leave_text[name].setdefault(plan_date, {})[columns["TomorrowPlan"]] = tomorrow_plan
        relevant_dates = [work_date, target]
        if tomorrow_plan:
            relevant_dates.append(plan_date)
        if any(day.year == year and day.month == month for day in relevant_dates):
            people.add(name)

    output_people = []
    for name in sorted(people):
        person_warnings: list[str] = []
        person_rows: list[dict[str, Any]] = []
        physical_index = 0

        for day in month_days(year, month):
            summary = summaries[name].get(day, "")
            att = attendance[name].get(day)
            raw_location = (att or {}).get(columns["WorkLocation"], "").strip()
            location_kind = location_map.get(raw_location)
            spreadsheet_row = data_start_row + physical_index

            if day.weekday() >= 5 or day in holidays:
                label = holidays.get(day, holiday_label)
                person_rows.append(
                    row_obj(
                        name=name,
                        day=day,
                        spreadsheet_row=spreadsheet_row,
                        kind="holiday",
                        content=label,
                        red_m=True,
                    )
                )
                physical_index += 1
                continue

            if raw_location and location_kind is None:
                person_warnings.append(
                    f"{day.isoformat()}: unmapped WorkLocation {raw_location!r}; emitted summary-only row."
                )

            source = {
                "summary_date": day.isoformat() if summary else None,
                "attendance_from": (att or {}).get(columns["WorkDate"]),
                "work_location": raw_location or None,
            }

            if location_kind == "leave":
                person_rows.append(
                    row_obj(
                        name=name,
                        day=day,
                        spreadsheet_row=spreadsheet_row,
                        kind="leave",
                        content=leave_label,
                        red_m=True,
                        source=source,
                    )
                )
                physical_index += 1
                continue

            half_kind, half_warnings = detect_half_day(
                leave_text[name].get(day),
                summary,
                columns,
                morning_half_label,
                afternoon_half_label,
            )
            person_warnings.extend(f"{day.isoformat()}: {warning}" for warning in half_warnings)

            def business_row(start: float, end: float, row_number: int) -> dict[str, Any]:
                if location_kind == "external":
                    return row_obj(
                        name=name,
                        day=day,
                        spreadsheet_row=row_number,
                        kind="external",
                        start=start,
                        end=end,
                        customer=infer_customer(att, summary, columns, customer_hints),
                        content=summary,
                        source=source,
                    )
                if location_kind == "internal":
                    return row_obj(
                        name=name,
                        day=day,
                        spreadsheet_row=row_number,
                        kind="internal",
                        start=start,
                        end=end,
                        customer=internal_label,
                        maintenance="N/A",
                        sales="N/A",
                        residence="N/A",
                        project_code="N/A",
                        project_name=internal_label,
                        content=summary,
                        source=source,
                    )
                return row_obj(
                    name=name,
                    day=day,
                    spreadsheet_row=row_number,
                    kind="summary_only",
                    content=summary,
                    source=source,
                )

            def half_row(label: str, start: float, end: float, row_number: int) -> dict[str, Any]:
                return row_obj(
                    name=name,
                    day=day,
                    spreadsheet_row=row_number,
                    kind="half_day",
                    start=start,
                    end=end,
                    customer=label,
                    project_name=label,
                    content=label,
                    source=source,
                )

            if half_kind == "morning":
                person_rows.append(
                    half_row(morning_half_label, work_start, half_boundary, spreadsheet_row)
                )
                physical_index += 1
                person_rows.append(
                    business_row(half_boundary, work_end, data_start_row + physical_index)
                )
                physical_index += 1
            elif half_kind == "afternoon":
                person_rows.append(business_row(work_start, half_boundary, spreadsheet_row))
                physical_index += 1
                person_rows.append(
                    half_row(
                        afternoon_half_label,
                        half_boundary,
                        work_end,
                        data_start_row + physical_index,
                    )
                )
                physical_index += 1
            elif location_kind in {"external", "internal"}:
                person_rows.append(business_row(work_start, work_end, spreadsheet_row))
                physical_index += 1
            else:
                person_rows.append(
                    row_obj(
                        name=name,
                        day=day,
                        spreadsheet_row=spreadsheet_row,
                        kind="summary_only" if summary else "blank",
                        content=summary,
                        source=source,
                    )
                )
                physical_index += 1

        output_people.append(
            {
                "name": name,
                "email": emails.get(name, ""),
                "row_count": len(person_rows),
                "rows": person_rows,
                "warnings": person_warnings,
            }
        )

    return {
        "year": year,
        "month": month,
        "data_start_row": data_start_row,
        "managed_columns": MANAGED_COLUMNS,
        "holidays": {day.isoformat(): label for day, label in sorted(holidays.items())},
        "people": output_people,
        "warnings": warnings,
    }


def main() -> None:
    args = parse_args()
    columns = parse_columns(args.column)
    plan = build_plan(
        load_rows(Path(args.csv), columns),
        year=args.year,
        month=args.month,
        holidays=parse_holidays(args.holiday, args.holiday_label),
        people_filter=set(args.person),
        columns=columns,
        location_map=parse_location_map(args.location_map),
        customer_hints=parse_customer_hints(args.customer_hint),
        location_shift=args.work_location_shift,
        data_start_row=args.data_start_row,
        work_start=args.work_start,
        work_end=args.work_end,
        half_boundary=args.half_boundary,
        holiday_label=args.holiday_label,
        leave_label=args.leave_label,
        internal_label=args.internal_label,
        morning_half_label=args.morning_half_label,
        afternoon_half_label=args.afternoon_half_label,
    )
    text = json.dumps(plan, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()
