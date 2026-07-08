# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This repo is a single-file, static web app: a **Fine-Kinney occupational risk assessment calculator** (`Эрсдэлийн зэрэг = Магадлал (P) × Өртөмж (E) × Үр дагавар (C)`). The UI copy is entirely in Mongolian. There is no backend, no build step, and no package manager — everything lives in `index.html` (HTML + inline CSS + inline vanilla JS).

## Development

There is no build/lint/test tooling in this repo. To work on it:

- Open `index.html` directly in a browser, or serve it locally, e.g. `python3 -m http.server` from the repo root and visit `http://localhost:8000/index.html`.
- Verify changes manually in a browser — there is no automated test suite.

## Architecture

Everything is in `index.html`, structured top to bottom as:

1. **Inline `<style>`** — theming via CSS custom properties on `:root`, with a `prefers-color-scheme: dark` override block. Reuse these variables (`--bg`, `--card-bg`, `--text`, `--muted`, `--border`, `--accent`) rather than hardcoding colors.
2. **Markup** — three `.card` sections: the input form (task name, P/E/C selects, control measure textarea), the live result card, and the risk record log table, plus a static reference table of risk-level ranges.
3. **Inline `<script>`**, in this order:
   - **Data tables**: `PROBABILITY`, `EXPOSURE`, `CONSEQUENCE` arrays (value + Mongolian label) populate the three `<select>` dropdowns. `LEVELS` defines the five risk bands (score range, label, color, description) used both for live scoring and the reference table.
   - **Live calculation**: `calculate()` reads the three select values, computes `R = P × E × C`, looks up the band via `getLevel(r)`, and updates the result card. Runs on `change` of any select and once on load.
   - **Persistence**: risk records are stored in `localStorage` under key `fineKinneyRecords` via `loadRecords()`/`saveRecords()`. `renderRecords()` re-renders the log table from storage on every mutation (add/delete/clear) — there is no separate app state, storage is the source of truth.
   - **Excel export**: `buildExcelWorkbook()` hand-builds an XML Spreadsheet (SpreadsheetML) string — not a real `.xlsx` — with per-risk-level cell coloring, downloaded as a `.xls` file via a Blob/`URL.createObjectURL`.

## Conventions

- Vanilla ES5-style JS (`var`, `function` expressions) — no modules, no framework, no build step. Match this style rather than introducing modern syntax that would need transpilation.
- All user-facing strings are Mongolian; keep new UI text consistent with the existing tone/terminology (e.g. "Эрсдэл" = risk, "Магадлал" = probability, "Өртөмж" = exposure, "Үр дагавар" = consequence).
- When adding a field to a risk record, update it in three places together: the form input, the object pushed in the `addRecordBtn` handler, and both `renderRecords()` (HTML table) and `buildExcelWorkbook()` (Excel export) so the log view and export stay in sync.
- User-supplied text rendered into the DOM (task name, control measure) must go through `escapeHtml()`; text written into the Excel XML must go through `excelEscape()`. Do not bypass these when adding new fields.
