# Clause Structure QA Tool

## Overview
A lightweight internal web application to help testers quickly validate the quality of AI-extracted document clause structures. The tool surfaces structural information with inline issue visualization and supports bilingual UI (EN/中文).

## Tech Stack
- Backend: FastAPI (Python)
- Frontend: Simple HTML + minimal JS (inline in main.py)
- No heavy frameworks - utilitarian design for internal testing

## Features
- Large textarea for pasting AI-extracted clause JSON
- JSON file upload as alternative input method
- Compact table output showing: Clause Number, Clause Title, Clause Page, Clause Path, Content (preview), Issues
- Content viewing: Click truncated preview to open full content in modal popup (read-only, scrollable)
- Inline issue visualization with row highlighting and badges
- Bilingual UI (EN/中文) with instant language switching and localStorage persistence
- Validation checks:
  1. Clause number continuity gaps (detects missing clauses)
  2. Missing or empty clause titles
  3. Missing or invalid page numbers

## Running the Application
```bash
python main.py
```
The server runs on port 5000.

## Project Structure
- `main.py` - Complete FastAPI application with embedded HTML frontend

## Input Format
JSON array of clause objects with fields:
- clause_number (string)
- clause_title (string)
- clause_page (string or number)
- clause_content (optional, viewable via modal)
- clause_path (array of strings)

## Recent Changes
- 2026-01-15: Added content viewing feature with modal popup
- 2026-01-15: Added bilingual UI support (EN/中文)
- 2026-01-15: Added JSON file upload option
- 2026-01-14: Initial implementation of Clause QA Tool
