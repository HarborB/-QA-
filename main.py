from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
import json

app = FastAPI(title="Clause QA Tool")

@app.get("/")
async def root():
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content='<html><body><p>Clause QA Tool - <a href="/app">Open App</a></p></body></html>', status_code=200)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

def normalize_clause_number(clause_number: str) -> str:
    if not clause_number:
        return ""
    return str(clause_number).rstrip('.')

def get_parent_path(clause_path: List[str]) -> str:
    if not clause_path or len(clause_path) < 2:
        return ""
    return " > ".join(clause_path[:-1])

def extract_last_number(clause_number: str) -> Optional[int]:
    normalized = normalize_clause_number(clause_number)
    if not normalized:
        return None
    parts = normalized.split('.')
    last_part = parts[-1]
    try:
        return int(last_part)
    except ValueError:
        return None

def validate_clauses(clauses: List[dict]) -> dict:
    issues = {
        "continuity_gaps": [],
        "empty_titles": [],
        "invalid_pages": []
    }
    
    siblings_by_parent = {}
    
    for i, clause in enumerate(clauses):
        clause_number = clause.get("clause_number", "")
        clause_title = clause.get("clause_title", "")
        clause_page = clause.get("clause_page", "")
        clause_path = clause.get("clause_path", [])
        
        if not clause_title or not str(clause_title).strip():
            issues["empty_titles"].append({
                "index": i + 1,
                "clause_number": clause_number or "(no number)"
            })
        
        page_str = str(clause_page).strip() if clause_page is not None else ""
        if not page_str:
            issues["invalid_pages"].append({
                "index": i + 1,
                "clause_number": clause_number or "(no number)",
                "reason": "empty"
            })
        else:
            try:
                float(page_str)
            except ValueError:
                issues["invalid_pages"].append({
                    "index": i + 1,
                    "clause_number": clause_number or "(no number)",
                    "reason": f"non-numeric: '{page_str}'"
                })
        
        if clause_path:
            parent_key = get_parent_path(clause_path)
            if parent_key not in siblings_by_parent:
                siblings_by_parent[parent_key] = []
            siblings_by_parent[parent_key].append({
                "index": i + 1,
                "clause_number": clause_number,
                "last_num": extract_last_number(clause_number)
            })
    
    for parent_key, siblings in siblings_by_parent.items():
        valid_siblings = [s for s in siblings if s["last_num"] is not None]
        valid_siblings.sort(key=lambda x: x["last_num"])
        
        for j in range(1, len(valid_siblings)):
            prev = valid_siblings[j - 1]
            curr = valid_siblings[j]
            expected = prev["last_num"] + 1
            actual = curr["last_num"]
            
            if actual != expected:
                issues["continuity_gaps"].append({
                    "parent": parent_key or "(root level)",
                    "after_clause": prev["clause_number"],
                    "before_clause": curr["clause_number"],
                    "expected_next": expected,
                    "found": actual
                })
    
    return issues

def extract_display_fields(clauses: List[dict]) -> List[dict]:
    result = []
    for clause in clauses:
        result.append({
            "clause_number": normalize_clause_number(str(clause.get("clause_number", ""))),
            "clause_title": clause.get("clause_title", ""),
            "clause_page": clause.get("clause_page", ""),
            "clause_path": clause.get("clause_path", [])
        })
    return result

@app.get("/app", response_class=HTMLResponse)
async def home():
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Clause QA Tool</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        html {
            font-size: 15px;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", Roboto, Oxygen, Ubuntu, sans-serif;
            background: #f8f9fa;
            color: #1a1a1a;
            line-height: 1.5;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1140px;
            margin: 0 auto;
            padding: 48px 32px;
        }
        
        .page-header {
            margin-bottom: 40px;
        }
        
        .page-title {
            font-size: 1.75rem;
            font-weight: 600;
            color: #111;
            letter-spacing: -0.02em;
            margin-bottom: 8px;
        }
        
        .page-subtitle {
            font-size: 0.9rem;
            color: #6b7280;
            font-weight: 400;
        }
        
        .card {
            background: #fff;
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            padding: 28px;
            margin-bottom: 24px;
        }
        
        .input-section {
            background: #fff;
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            padding: 28px;
            margin-bottom: 32px;
        }
        
        .input-label {
            display: block;
            font-size: 0.8rem;
            font-weight: 500;
            color: #374151;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 12px;
        }
        
        textarea {
            width: 100%;
            height: 220px;
            font-family: "SF Mono", "Fira Code", "Monaco", "Consolas", monospace;
            font-size: 0.85rem;
            line-height: 1.6;
            padding: 16px 18px;
            background: #fafafa;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            resize: vertical;
            color: #333;
        }
        
        textarea::placeholder {
            color: #9ca3af;
        }
        
        textarea:focus {
            outline: none;
            border-color: #3b82f6;
            background: #fff;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }
        
        .btn-primary {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: #2563eb;
            color: #fff;
            font-size: 0.9rem;
            font-weight: 500;
            border: none;
            padding: 12px 28px;
            border-radius: 8px;
            cursor: pointer;
            margin-top: 16px;
        }
        
        .btn-primary:hover {
            background: #1d4ed8;
        }
        
        .btn-primary:disabled {
            background: #d1d5db;
            color: #9ca3af;
            cursor: not-allowed;
        }
        
        .error-message {
            background: #fef2f2;
            border: 1px solid #fecaca;
            color: #b91c1c;
            padding: 16px 20px;
            border-radius: 8px;
            margin-bottom: 24px;
            font-size: 0.9rem;
        }
        
        .results {
            display: none;
        }
        
        .section-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
            padding-bottom: 16px;
            border-bottom: 1px solid #f0f0f0;
        }
        
        .section-title {
            font-size: 1rem;
            font-weight: 600;
            color: #111;
            letter-spacing: -0.01em;
        }
        
        .issues-section {
            background: #fff;
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            padding: 28px;
            margin-bottom: 24px;
        }
        
        .issue-category {
            margin-bottom: 20px;
        }
        
        .issue-category:last-child {
            margin-bottom: 0;
        }
        
        .issue-category-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 12px;
        }
        
        .issue-category-title {
            font-size: 0.85rem;
            font-weight: 500;
            color: #4b5563;
        }
        
        .issue-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        
        .issue-list li {
            background: #fffbeb;
            border-left: 3px solid #f59e0b;
            padding: 10px 14px;
            margin-bottom: 6px;
            font-size: 0.85rem;
            color: #78350f;
            border-radius: 0 6px 6px 0;
        }
        
        .issue-list.error-list li {
            background: #fef2f2;
            border-left-color: #ef4444;
            color: #991b1b;
        }
        
        .no-issues {
            display: flex;
            align-items: center;
            gap: 8px;
            color: #059669;
            font-size: 0.9rem;
            font-weight: 500;
        }
        
        .no-issues::before {
            content: "";
            display: inline-block;
            width: 8px;
            height: 8px;
            background: #10b981;
            border-radius: 50%;
        }
        
        .table-section {
            background: #fff;
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            padding: 28px;
            overflow: hidden;
        }
        
        .table-wrapper {
            overflow-x: auto;
            margin: 0 -28px -28px -28px;
            padding: 0 28px 28px 28px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85rem;
        }
        
        th {
            text-align: left;
            padding: 12px 16px;
            background: #f9fafb;
            font-weight: 600;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #6b7280;
            border-bottom: 1px solid #e5e7eb;
            white-space: nowrap;
        }
        
        td {
            padding: 14px 16px;
            border-bottom: 1px solid #f3f4f6;
            color: #374151;
            vertical-align: top;
        }
        
        tbody tr:hover {
            background: #fafafa;
        }
        
        tbody tr:last-child td {
            border-bottom: none;
        }
        
        .col-number {
            width: 120px;
            font-weight: 500;
            font-family: "SF Mono", "Fira Code", monospace;
            font-size: 0.85rem;
            color: #111;
        }
        
        .col-title {
            min-width: 200px;
            max-width: 400px;
            word-wrap: break-word;
        }
        
        .col-page {
            width: 80px;
            text-align: center;
        }
        
        .col-path {
            min-width: 160px;
        }
        
        .clause-path {
            font-family: "SF Mono", "Fira Code", monospace;
            font-size: 0.8rem;
            color: #6366f1;
            background: #eef2ff;
            padding: 4px 8px;
            border-radius: 4px;
            display: inline-block;
        }
        
        .empty-value {
            color: #9ca3af;
            font-style: italic;
            font-size: 0.8rem;
        }
        
        .badge {
            display: inline-flex;
            align-items: center;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        
        .badge-success {
            background: #ecfdf5;
            color: #059669;
        }
        
        .badge-warning {
            background: #fffbeb;
            color: #b45309;
        }
        
        .badge-error {
            background: #fef2f2;
            color: #dc2626;
        }
        
        .badge-count {
            background: #f3f4f6;
            color: #4b5563;
        }
    </style>
</head>
<body>
    <div class="container">
        <header class="page-header">
            <h1 class="page-title">Clause Structure QA Tool</h1>
            <p class="page-subtitle">Validate structural consistency of AI-extracted document clauses</p>
        </header>
        
        <div class="input-section">
            <label class="input-label" for="jsonInput">Input JSON</label>
            <textarea id="jsonInput" placeholder='[
  {
    "clause_number": "1",
    "clause_title": "Introduction",
    "clause_page": "1",
    "clause_content": "...",
    "clause_path": ["1"]
  },
  {
    "clause_number": "2.1",
    "clause_title": "Definitions",
    "clause_page": "3",
    "clause_content": "...",
    "clause_path": ["2", "2.1"]
  }
]'></textarea>
            <button id="submitBtn" class="btn-primary" onclick="analyzeJson()">Analyze Clauses</button>
        </div>
        
        <div id="errorDiv" class="error-message" style="display: none;"></div>
        
        <div id="results" class="results">
            <div class="issues-section">
                <div class="section-header">
                    <h2 class="section-title">Validation Results</h2>
                </div>
                <div id="issuesSummary"></div>
            </div>
            
            <div class="table-section">
                <div class="section-header">
                    <h2 class="section-title">Clause Structure</h2>
                    <span id="clauseCount"></span>
                </div>
                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th class="col-number">Number</th>
                                <th class="col-title">Title</th>
                                <th class="col-page">Page</th>
                                <th class="col-path">Path</th>
                            </tr>
                        </thead>
                        <tbody id="clauseTable"></tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script>
        function escapeHtml(text) {
            if (text === null || text === undefined) return '';
            const div = document.createElement('div');
            div.textContent = String(text);
            return div.innerHTML;
        }
        
        async function analyzeJson() {
            const input = document.getElementById('jsonInput').value.trim();
            const errorDiv = document.getElementById('errorDiv');
            const results = document.getElementById('results');
            const btn = document.getElementById('submitBtn');
            
            errorDiv.style.display = 'none';
            results.style.display = 'none';
            
            if (!input) {
                errorDiv.textContent = 'Please paste JSON data into the textarea.';
                errorDiv.style.display = 'block';
                return;
            }
            
            let parsed;
            try {
                parsed = JSON.parse(input);
            } catch (e) {
                errorDiv.textContent = 'Invalid JSON: ' + e.message;
                errorDiv.style.display = 'block';
                return;
            }
            
            if (!Array.isArray(parsed)) {
                errorDiv.textContent = 'Expected a JSON array of clause objects.';
                errorDiv.style.display = 'block';
                return;
            }
            
            btn.disabled = true;
            btn.textContent = 'Analyzing...';
            
            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({clauses: parsed})
                });
                
                if (!response.ok) {
                    throw new Error('Server error: ' + response.status);
                }
                
                const data = await response.json();
                renderResults(data);
                results.style.display = 'block';
            } catch (e) {
                errorDiv.textContent = 'Error: ' + e.message;
                errorDiv.style.display = 'block';
            } finally {
                btn.disabled = false;
                btn.textContent = 'Analyze Clauses';
            }
        }
        
        function renderResults(data) {
            const issuesSummary = document.getElementById('issuesSummary');
            const clauseTable = document.getElementById('clauseTable');
            const clauseCount = document.getElementById('clauseCount');
            
            clauseCount.innerHTML = `<span class="badge badge-count">${escapeHtml(data.clauses.length)} clauses</span>`;
            
            let issuesHtml = '';
            const issues = data.issues;
            
            const totalIssues = issues.continuity_gaps.length + issues.empty_titles.length + issues.invalid_pages.length;
            
            if (totalIssues === 0) {
                issuesHtml = '<p class="no-issues">No structural issues detected</p>';
            } else {
                if (issues.continuity_gaps.length > 0) {
                    issuesHtml += `<div class="issue-category">
                        <div class="issue-category-header">
                            <span class="issue-category-title">Clause Number Continuity Gaps</span>
                            <span class="badge badge-warning">${escapeHtml(issues.continuity_gaps.length)}</span>
                        </div>
                        <ul class="issue-list">`;
                    for (const gap of issues.continuity_gaps) {
                        issuesHtml += `<li>Under "${escapeHtml(gap.parent)}": Expected ${escapeHtml(gap.expected_next)} after "${escapeHtml(gap.after_clause)}", found "${escapeHtml(gap.before_clause)}" (${escapeHtml(gap.found)})</li>`;
                    }
                    issuesHtml += '</ul></div>';
                }
                
                if (issues.empty_titles.length > 0) {
                    issuesHtml += `<div class="issue-category">
                        <div class="issue-category-header">
                            <span class="issue-category-title">Missing or Empty Titles</span>
                            <span class="badge badge-warning">${escapeHtml(issues.empty_titles.length)}</span>
                        </div>
                        <ul class="issue-list">`;
                    for (const item of issues.empty_titles) {
                        issuesHtml += `<li>Row ${escapeHtml(item.index)}: Clause "${escapeHtml(item.clause_number)}" has no title</li>`;
                    }
                    issuesHtml += '</ul></div>';
                }
                
                if (issues.invalid_pages.length > 0) {
                    issuesHtml += `<div class="issue-category">
                        <div class="issue-category-header">
                            <span class="issue-category-title">Invalid or Missing Page Numbers</span>
                            <span class="badge badge-error">${escapeHtml(issues.invalid_pages.length)}</span>
                        </div>
                        <ul class="issue-list error-list">`;
                    for (const item of issues.invalid_pages) {
                        issuesHtml += `<li>Row ${escapeHtml(item.index)}: Clause "${escapeHtml(item.clause_number)}" — ${escapeHtml(item.reason)}</li>`;
                    }
                    issuesHtml += '</ul></div>';
                }
            }
            
            issuesSummary.innerHTML = issuesHtml;
            
            let tableHtml = '';
            for (const clause of data.clauses) {
                const num = clause.clause_number ? `<span class="col-number">${escapeHtml(clause.clause_number)}</span>` : '<span class="empty-value">—</span>';
                const title = clause.clause_title ? escapeHtml(clause.clause_title) : '<span class="empty-value">—</span>';
                const page = clause.clause_page !== '' && clause.clause_page !== null ? escapeHtml(clause.clause_page) : '<span class="empty-value">—</span>';
                const path = clause.clause_path && clause.clause_path.length > 0 
                    ? `<span class="clause-path">[${clause.clause_path.map(p => escapeHtml(p)).join(', ')}]</span>` 
                    : '<span class="empty-value">—</span>';
                
                tableHtml += `<tr>
                    <td class="col-number">${clause.clause_number ? escapeHtml(clause.clause_number) : '<span class="empty-value">—</span>'}</td>
                    <td class="col-title">${title}</td>
                    <td class="col-page">${page}</td>
                    <td class="col-path">${path}</td>
                </tr>`;
            }
            
            clauseTable.innerHTML = tableHtml;
        }
    </script>
</body>
</html>'''
    return HTMLResponse(content=html_content)

class AnalyzeRequest(BaseModel):
    clauses: List[dict]

@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
    clauses = request.clauses
    display_clauses = extract_display_fields(clauses)
    issues = validate_clauses(clauses)
    return {
        "clauses": display_clauses,
        "issues": issues
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
