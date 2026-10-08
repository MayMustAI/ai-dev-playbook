# Google Sheets write shapes

Read this reference before the first write. Derive all row numbers from inspected template metadata and the row-plan JSON; do not assume the example defaults match the user's template.

## Template variables

Record:

- `data_start_row`: first 1-based data row; pass the same value to `build_resource_rows.py`
- `template_day_row_count`: number of data rows reserved by the template before its notes/footer
- `note_start_row`: first 1-based notes/footer row
- `target_count`: emitted row count for the person

The bundled script manages columns A:M and emits formulas for column F. Confirm the user's template uses that shape before writing.

## Row adjustment

- If `target_count > template_day_row_count`, insert the difference immediately before `note_start_row`.
- If `target_count < template_day_row_count`, delete surplus data rows from `data_start_row + target_count` through the final reserved data row.
- Write A:M from `data_start_row` through `data_start_row + target_count - 1`.

Perform structural changes before cell writes so formulas use final row numbers. Preserve merged headers, column widths, borders, notes, and footer rows.

## Cell encoding

- Write strings and numbers as typed user-entered values.
- A formula cell has `{"formula": "=IF(OR(D3=\"\",E3=\"\"),\"\",E3-D3)"}`; write it as `userEnteredValue.formulaValue`. Preserve the blank-time guard when translating to Sheets or XLSX.
- Write explicit empty strings where template residue must be cleared.
- For rows with `red_m: true`, apply red text only to column M. Do not recolor the row.

## Safety

- Keep uncertain customer and project fields blank.
- Never merge cells or overwrite the source template.
- Re-read A:M after each batch update and compare dates, formulas, row count, and red labels with the JSON plan.
