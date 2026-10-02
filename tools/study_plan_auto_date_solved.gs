/**
 * Auto-fills "Date Solved" the moment "Status" is set to "Solved" on the
 * "Study Plan" tab of Study_Plan_Progress.xlsx (imported into Google Sheets).
 *
 * Install:
 *   1. Open the Google Sheet.
 *   2. Extensions -> Apps Script.
 *   3. Delete the boilerplate `function myFunction() {}` and paste this file's
 *      contents in its place.
 *   4. Save (Ctrl+S / Cmd+S). No deployment or authorization step needed --
 *      onEdit(e) is a "simple trigger" and Google runs it automatically for
 *      edits made directly in the sheet (not for edits made via API/Apps
 *      Script itself, and not for values arriving through a formula).
 *   5. Go back to the sheet and change a Status cell to "Solved" -- Date
 *      Solved fills in with today's date immediately.
 *
 * Behavior:
 *   - Only fires on the "Study Plan" tab.
 *   - Only fires when the edited cell is in the Status column.
 *   - Matches "Solved" case-insensitively and ignores stray leading/trailing
 *     spaces, so it still fires even if the value was typed by hand instead
 *     of picked from the dropdown (e.g. "solved", "SOLVED ").
 *   - Normalizes the Status cell itself back to the canonical "Solved" text
 *     so it stays consistent with the dropdown list and every COUNTIF/
 *     COUNTIFS formula on the other tabs (those match on the exact string
 *     "Solved").
 *   - Only fills Date Solved if it is currently blank -- it never overwrites
 *     a date you already recorded, and it never clears a date if you move
 *     Status away from "Solved" later.
 *   - Handles multi-row edits too (e.g. pasting a column of statuses, or
 *     dragging the fill handle down several rows).
 */
function onEdit(e) {
  var STATUS_COL = 9;   // column I
  var DATE_COL = 11;    // column K
  var FIRST_DATA_ROW = 2;
  var SHEET_NAME = "Study Plan";

  var range = e.range;
  var sheet = range.getSheet();
  if (sheet.getName() !== SHEET_NAME) return;

  var startCol = range.getColumn();
  var endCol = range.getLastColumn();
  if (endCol < STATUS_COL || startCol > STATUS_COL) return;

  var startRow = Math.max(range.getRow(), FIRST_DATA_ROW);
  var endRow = range.getLastRow();
  if (endRow < FIRST_DATA_ROW) return;

  for (var row = startRow; row <= endRow; row++) {
    var statusCell = sheet.getRange(row, STATUS_COL);
    var raw = statusCell.getValue();
    var normalized = String(raw).trim();

    if (normalized.toLowerCase() === "solved") {
      if (normalized !== "Solved") {
        statusCell.setValue("Solved"); // keep in sync with the dropdown + COUNTIF formulas
      }
      var dateCell = sheet.getRange(row, DATE_COL);
      if (!dateCell.getValue()) {
        var now = new Date();
        var today = new Date(now.getFullYear(), now.getMonth(), now.getDate()); // strip time-of-day
        dateCell.setValue(today);
        dateCell.setNumberFormat("yyyy-mm-dd");
      }
    }
  }
}
