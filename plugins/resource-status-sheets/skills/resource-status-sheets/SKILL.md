---
name: resource-status-sheets
description: Create monthly per-person Google Sheets resource or timesheet reports from DailyUpdates CSV exports and a user-provided native Google Sheets template. Use when the user asks to generate, repeat, export, or automate monthly resource-status sheets, including configurable CSV headers, same-day or next-business-day WorkLocation mapping, holidays, leave, half-day rows, customer hints, and one spreadsheet per person.
---

# Resource Status Sheets

Create one native Google Sheet per submitter while preserving the user's template. Build and inspect a deterministic JSON row plan before any Drive or Sheets mutation.

## Requirements and inputs

Use available Google Drive and Google Sheets connectors for discovery, duplication, metadata, and batch updates. If they are unavailable, stop and tell the user which capability is missing; do not invent file or folder URLs. Use a spreadsheet/file skill only for an explicitly requested local Excel export after the Google Sheets output is verified.

Require these runtime inputs; never reuse values from an earlier month unless the user confirms them:

- absolute DailyUpdates CSV path
- target year and month
- native Google Sheets template URL or ID and source tab
- destination Drive folder URL or ID
- file naming pattern
- holiday locale plus organization-specific non-working dates
- whether `WorkLocation` applies on the same day or next business day

Also confirm the template's first data row, reserved day-row count, notes/footer start row, and that managed columns A:M match the emitted schema. Ask only for values that cannot be safely discovered from the template, CSV headers, or current request.

## Plan rows

Resolve this skill's directory and run its bundled script by relative path; never use an author's home-directory path:

```bash
python3 <skill-dir>/scripts/build_resource_rows.py \
  --csv "/absolute/path/DailyUpdates.csv" \
  --year 2026 \
  --month 5 \
  --work-location-shift next-business-day \
  --holiday 2026-05-01="Organization holiday" \
  --holiday 2026-05-05="Public holiday" \
  --customer-hint "Acme Korea=Acme" \
  --output /tmp/resource-rows.json
```

Use `--column LOGICAL=CSV_HEADER` when export headers differ. Required logical fields are `WorkDate`, `SubmitterName`, `WorkLocation`, and `TodaySummary`; optional fields are `SubmitterEmail`, `TomorrowPlan`, and `Note`.

Use repeatable `--location-map VALUE=internal|external|leave` for organization-specific location labels. Korean defaults are bundled for `출근`, `재택`, `내근`, `외근`, and `휴가`; explicit mappings override or extend them. Customer inference is intentionally empty unless `--customer-hint TEXT[=CANONICAL]` is provided.

Pass template-specific `--data-start-row`, time boundaries, and output labels when defaults do not match. Run `--help` for the complete interface. Review all top-level and per-person warnings before creating files; unresolved warnings require user review rather than guessed data.

## Holidays

Verify public holidays for the requested locale and month using current authoritative sources. Include observed/substitute holidays and organization-specific dates only when supported by the source, template, or user. Record the exact dates passed to the script in the final report.

## Create and populate

1. Read template metadata and A:M cells before editing. Record spreadsheet ID, source tab, sheet ID, data row bounds, and footer position.
2. Create a destination month folder only when requested and supported. Return the connector-provided URL.
3. Duplicate the native template into one independent spreadsheet per JSON submitter. Do not regenerate an XLSX and re-import it; conversion can alter layout and formatting.
4. Use the confirmed naming pattern. Sanitize only characters invalid for Drive titles and report any change.
5. Before the first write, read [references/google-sheets-write-shapes.md](references/google-sheets-write-shapes.md).
6. Adjust reserved data rows to each person's `row_count`, then write A:M beginning at the same `data_start_row` passed to the script.
7. Write emitted formula objects as formulas in column F. Apply red font only to column M when `red_m` is true.
8. Preserve headers, merged cells, widths, borders, notes/footer, and all unmanaged formatting.

## Default business rules

- `TodaySummary` stays on its `WorkDate`.
- Half-day declarations in `Note` and `TodaySummary` apply on `WorkDate`; `TomorrowPlan` applies on the next business day. This timing is independent of the `WorkLocation` shift. Conflicting morning/afternoon declarations require user review.
- In `next-business-day` mode, `WorkLocation` moves to the next weekday not listed in `--holiday`; weekend/holiday entries continue to the next business day.
- Weekends and configured holidays override summaries and emit a red holiday label.
- `internal` emits configured work hours, the internal label for customer/project, `N/A` for other known non-applicable fields, and `TodaySummary` as content.
- `external` emits configured work hours and summary; customer is filled only by an explicit customer hint. Uncertain customer/project fields remain blank.
- `leave` emits one row with a red leave label only in work content.
- Morning half-day emits a leave row from work start to half boundary, then a work row to work end. Afternoon half-day reverses the order.
- Priority is `holiday > leave > half-day > external > internal > summary-only`.

If the user's organization follows different rules, express supported differences with script flags. Do not silently change the script or template semantics during a monthly run.

Only include submitters with a source date, shifted location date, or nonempty tomorrow-plan date in the target month. Keep preceding-month records when they affect the target month.

## XLSX export

After verifying the native Sheets file, export to XLSX only when requested. Use the Spreadsheets skill for post-processing and visual verification:

- Preserve the script's guarded column-F formulas so blank start/end times produce blank hours.
- Wrap column M text, align it to the top, and increase row heights to show embedded newlines.
- Reopen or render the exported workbook; verify holiday/leave hour cells remain blank, multiline content is visible, and no `####` appears.

## Verify and report

Re-read every output's A:M values and relevant column-M formatting. Confirm one file per selected submitter, every calendar date, business-day shifting, formula cells, holiday/leave colors, half-day double rows, and preserved footer/layout. Return the destination folder, compact file/link list, holidays used, warnings or blanks needing human review, and any local exports requested.
