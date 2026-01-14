from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
import json

app = FastAPI(title="Clause QA Tool")

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

@app.get("/", response_class=HTMLResponse)
async def home():
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Clause QA Tool</title>
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        h1 { color: #333; margin-bottom: 10px; }
        .subtitle { color: #666; margin-bottom: 20px; }
        .input-section {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        textarea {
            width: 100%;
            height: 200px;
            font-family: monospace;
            font-size: 13px;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            resize: vertical;
        }
        textarea:focus { outline: none; border-color: #007bff; }
        button {
            background: #007bff;
            color: white;
            border: none;
            padding: 12px 24px;
            font-size: 16px;
            border-radius: 4px;
            cursor: pointer;
            margin-top: 10px;
        }
        button:hover { background: #0056b3; }
        button:disabled { background: #ccc; cursor: not-allowed; }
        .error {
            background: #fee;
            border: 1px solid #f00;
            color: #c00;
            padding: 15px;
            border-radius: 4px;
            margin: 20px 0;
        }
        .results { display: none; }
        .issues-section {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .issues-section h2 { margin-top: 0; color: #333; }
        .issue-category { margin-bottom: 15px; }
        .issue-category h3 { margin: 0 0 8px 0; font-size: 14px; color: #555; }
        .issue-list { list-style: none; padding: 0; margin: 0; }
        .issue-list li {
            background: #fff3cd;
            border-left: 3px solid #ffc107;
            padding: 8px 12px;
            margin-bottom: 5px;
            font-size: 13px;
        }
        .issue-list.error-list li {
            background: #f8d7da;
            border-left-color: #dc3545;
        }
        .no-issues { color: #28a745; font-weight: 500; }
        .table-section {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            overflow-x: auto;
        }
        .table-section h2 { margin-top: 0; color: #333; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; }
        th, td { text-align: left; padding: 10px 12px; border-bottom: 1px solid #eee; }
        th {
            background: #f8f9fa;
            font-weight: 600;
            color: #333;
            position: sticky;
            top: 0;
        }
        tr:hover { background: #f8f9fa; }
        .clause-path { font-family: monospace; font-size: 12px; color: #666; }
        .empty-value { color: #999; font-style: italic; }
        .count-badge {
            background: #dc3545;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            margin-left: 8px;
        }
        .count-badge.warning { background: #ffc107; color: #333; }
        .count-badge.success { background: #28a745; }
    </style>
</head>
<body>
    <h1>Clause Structure QA Tool</h1>
    <p class="subtitle">Paste AI-extracted clause JSON to validate structural consistency</p>
    
    <div class="input-section">
        <textarea id="jsonInput" placeholder='Paste JSON array here, e.g.:
[
  {
    "clause_number": "1",
    "clause_title": "Introduction",
    "clause_page": "1",
    "clause_content": "...",
    "clause_path": ["1"]
  },
  ...
]'></textarea>
        <button id="submitBtn" onclick="analyzeJson()">Analyze Clauses</button>
    </div>
    
    <div id="errorDiv" class="error" style="display: none;"></div>
    
    <div id="results" class="results">
        <div class="issues-section">
            <h2>Validation Issues</h2>
            <div id="issuesSummary"></div>
        </div>
        
        <div class="table-section">
            <h2>Clause Structure <span id="clauseCount"></span></h2>
            <table>
                <thead>
                    <tr>
                        <th>Clause Number</th>
                        <th>Clause Title</th>
                        <th>Clause Page</th>
                        <th>Clause Path</th>
                    </tr>
                </thead>
                <tbody id="clauseTable"></tbody>
            </table>
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
            
            clauseCount.innerHTML = `<span class="count-badge success">${escapeHtml(data.clauses.length)} clauses</span>`;
            
            let issuesHtml = '';
            const issues = data.issues;
            
            const totalIssues = issues.continuity_gaps.length + issues.empty_titles.length + issues.invalid_pages.length;
            
            if (totalIssues === 0) {
                issuesHtml = '<p class="no-issues">No structural issues detected.</p>';
            } else {
                if (issues.continuity_gaps.length > 0) {
                    issuesHtml += `<div class="issue-category">
                        <h3>Clause Number Continuity Gaps <span class="count-badge warning">${escapeHtml(issues.continuity_gaps.length)}</span></h3>
                        <ul class="issue-list">`;
                    for (const gap of issues.continuity_gaps) {
                        issuesHtml += `<li>Under "${escapeHtml(gap.parent)}": Expected ${escapeHtml(gap.expected_next)} after "${escapeHtml(gap.after_clause)}", but found "${escapeHtml(gap.before_clause)}" (${escapeHtml(gap.found)})</li>`;
                    }
                    issuesHtml += '</ul></div>';
                }
                
                if (issues.empty_titles.length > 0) {
                    issuesHtml += `<div class="issue-category">
                        <h3>Missing/Empty Titles <span class="count-badge warning">${escapeHtml(issues.empty_titles.length)}</span></h3>
                        <ul class="issue-list">`;
                    for (const item of issues.empty_titles) {
                        issuesHtml += `<li>Row ${escapeHtml(item.index)}: Clause "${escapeHtml(item.clause_number)}" has no title</li>`;
                    }
                    issuesHtml += '</ul></div>';
                }
                
                if (issues.invalid_pages.length > 0) {
                    issuesHtml += `<div class="issue-category">
                        <h3>Invalid/Missing Page Numbers <span class="count-badge warning">${escapeHtml(issues.invalid_pages.length)}</span></h3>
                        <ul class="issue-list error-list">`;
                    for (const item of issues.invalid_pages) {
                        issuesHtml += `<li>Row ${escapeHtml(item.index)}: Clause "${escapeHtml(item.clause_number)}" - ${escapeHtml(item.reason)}</li>`;
                    }
                    issuesHtml += '</ul></div>';
                }
            }
            
            issuesSummary.innerHTML = issuesHtml;
            
            let tableHtml = '';
            for (const clause of data.clauses) {
                const num = clause.clause_number ? escapeHtml(clause.clause_number) : '<span class="empty-value">(empty)</span>';
                const title = clause.clause_title ? escapeHtml(clause.clause_title) : '<span class="empty-value">(empty)</span>';
                const page = clause.clause_page !== '' && clause.clause_page !== null ? escapeHtml(clause.clause_page) : '<span class="empty-value">(empty)</span>';
                const path = clause.clause_path && clause.clause_path.length > 0 
                    ? `<span class="clause-path">[${clause.clause_path.map(p => escapeHtml(p)).join(', ')}]</span>` 
                    : '<span class="empty-value">(empty)</span>';
                
                tableHtml += `<tr>
                    <td>${num}</td>
                    <td>${title}</td>
                    <td>${page}</td>
                    <td>${path}</td>
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
