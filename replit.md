# Clause Structure QA Tool

## Overview
A lightweight internal web application to help testers quickly validate the quality of AI-extracted document clause structures. The tool compresses output and surfaces only structural information so testers can assess correctness at a glance.

## Tech Stack
- Backend: FastAPI (Python)
- Frontend: Simple HTML + minimal JS (inline in main.py)
- No heavy frameworks - utilitarian design for internal testing

## Features
- Large textarea for pasting AI-extracted clause JSON
- Compact table output showing: Clause Number, Clause Title, Clause Page, Clause Path
- clause_content is never displayed (intentionally hidden)
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
- clause_content (ignored in output)
- clause_path (array of strings)

## Recent Changes
- 2026-01-14: Initial implementation of Clause QA Tool
