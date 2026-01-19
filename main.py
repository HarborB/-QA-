from fastapi import FastAPI
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import json

app = FastAPI(title="Clause QA Tool")

@app.get("/")
async def root():
    return HTMLResponse(content='<!DOCTYPE html><html><head><meta http-equiv="refresh" content="0;url=/app"></head><body></body></html>', status_code=200)

@app.get("/health")
async def health_check():
    return PlainTextResponse(content="ok", status_code=200)

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
                "index": i,
                "clause_number": clause_number or "(no number)"
            })
        
        page_str = str(clause_page).strip() if clause_page is not None else ""
        if not page_str:
            issues["invalid_pages"].append({
                "index": i,
                "clause_number": clause_number or "(no number)",
                "reason": "empty"
            })
        else:
            try:
                float(page_str)
            except ValueError:
                issues["invalid_pages"].append({
                    "index": i,
                    "clause_number": clause_number or "(no number)",
                    "reason": f"non-numeric: '{page_str}'"
                })
        
        if clause_path:
            parent_key = get_parent_path(clause_path)
            if parent_key not in siblings_by_parent:
                siblings_by_parent[parent_key] = []
            siblings_by_parent[parent_key].append({
                "index": i,
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
            "clause_path": clause.get("clause_path", []),
            "clause_content": clause.get("clause_content", "")
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
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }
        
        .header-content {
            flex: 1;
        }
        
        .lang-toggle {
            display: flex;
            gap: 4px;
            background: #f3f4f6;
            padding: 4px;
            border-radius: 6px;
        }
        
        .lang-btn {
            padding: 6px 12px;
            border: none;
            background: transparent;
            font-size: 0.8rem;
            font-weight: 500;
            color: #6b7280;
            cursor: pointer;
            border-radius: 4px;
            transition: all 0.15s;
        }
        
        .lang-btn:hover {
            color: #374151;
        }
        
        .lang-btn.active {
            background: #fff;
            color: #111;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
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
        
        .btn-clear {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: #f97316;
            color: #fff;
            font-size: 0.9rem;
            font-weight: 500;
            border: none;
            padding: 12px 28px;
            border-radius: 8px;
            cursor: pointer;
            transition: background 0.15s;
            margin-left: 12px;
        }
        
        .btn-clear:hover {
            background: #ea580c;
        }
        
        .upload-section {
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
        }
        
        .upload-label {
            display: block;
            font-size: 0.8rem;
            font-weight: 500;
            color: #374151;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 12px;
        }
        
        .file-input-wrapper {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .file-name {
            color: #6b7280;
            font-size: 0.9rem;
        }
        
        .file-name.has-file {
            color: #059669;
            font-weight: 500;
        }
        
        .file-input {
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            border: 0;
        }
        
        .file-input-btn {
            background: #f3f4f6;
            border: 1px solid #d1d5db;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 0.85rem;
            cursor: pointer;
            transition: background 0.15s;
        }
        
        .file-input-btn:hover {
            background: #e5e7eb;
        }
        
        .file-input::file-selector-button {
            background: #f3f4f6;
            border: 1px solid #d1d5db;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 0.85rem;
            font-weight: 500;
            color: #374151;
            cursor: pointer;
            transition: background 0.15s;
            margin-right: 12px;
        }
        
        .file-input::file-selector-button:hover {
            background: #e5e7eb;
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
        
        .col-content {
            min-width: 150px;
            max-width: 200px;
        }
        
        .content-preview {
            display: block;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 180px;
            color: #4b5563;
            font-size: 0.85rem;
            cursor: pointer;
            padding: 4px 8px;
            border-radius: 4px;
            background: #f9fafb;
            transition: background 0.15s;
        }
        
        .content-preview:hover {
            background: #e5e7eb;
            color: #111827;
        }
        
        .content-empty {
            color: #9ca3af;
            font-style: italic;
            font-size: 0.8rem;
        }
        
        /* Modal styles */
        .modal-overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }
        
        .modal-overlay.active {
            display: flex;
        }
        
        .modal {
            background: white;
            border-radius: 12px;
            width: 90%;
            max-width: 700px;
            max-height: 80vh;
            display: flex;
            flex-direction: column;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
        }
        
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 20px;
            border-bottom: 1px solid #e5e7eb;
        }
        
        .modal-title {
            font-weight: 600;
            color: #111827;
            font-size: 1rem;
        }
        
        .modal-close {
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            color: #6b7280;
            padding: 4px 8px;
            border-radius: 4px;
            line-height: 1;
        }
        
        .modal-close:hover {
            background: #f3f4f6;
            color: #111827;
        }
        
        .modal-body {
            padding: 20px;
            overflow-y: auto;
            flex: 1;
        }
        
        .modal-content-text {
            white-space: pre-wrap;
            word-wrap: break-word;
            font-size: 0.9rem;
            line-height: 1.6;
            color: #374151;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
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
        
        .row-issue {
            background: #fffbeb;
            border-left: 3px solid #f59e0b;
        }
        
        .row-issue-error {
            background: #fef2f2;
            border-left: 3px solid #ef4444;
        }
        
        .issue-badges {
            display: flex;
            gap: 4px;
            flex-wrap: wrap;
        }
        
        .inline-badge {
            display: inline-flex;
            align-items: center;
            font-size: 0.65rem;
            font-weight: 500;
            padding: 2px 6px;
            border-radius: 4px;
            cursor: help;
            white-space: nowrap;
        }
        
        .inline-badge-gap {
            background: #fef3c7;
            color: #92400e;
        }
        
        .inline-badge-title {
            background: #fed7aa;
            color: #9a3412;
        }
        
        .inline-badge-page {
            background: #fecaca;
            color: #b91c1c;
        }
        
        .issue-summary {
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
            align-items: center;
        }
        
        .issue-summary-item {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 0.85rem;
            color: #4b5563;
        }
        
        .col-issues {
            width: 120px;
            text-align: left;
        }
    </style>
</head>
<body>
    <div class="container">
        <header class="page-header">
            <div class="header-content">
                <h1 class="page-title" data-i18n="title">Clause Structure QA Tool</h1>
                <p class="page-subtitle" data-i18n="subtitle">Validate structural consistency of AI-extracted document clauses</p>
            </div>
            <div class="lang-toggle">
                <button class="lang-btn active" id="langEn" onclick="setLanguage('en')">EN</button>
                <button class="lang-btn" id="langZh" onclick="setLanguage('zh')">中文</button>
            </div>
        </header>
        
        <div class="input-section">
            <label class="input-label" for="jsonInput" data-i18n="inputJson">Input JSON</label>
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
            <button id="submitBtn" class="btn-primary" onclick="analyzeJson()" data-i18n="analyze">Analyze Clauses</button>
            <button class="btn-clear" onclick="clearInput()" data-i18n="clear">Clear</button>
            
            <div class="upload-section">
                <label class="upload-label" data-i18n="uploadLabel">Or Upload JSON File</label>
                <div class="file-input-wrapper">
                    <input type="file" id="fileInput" class="file-input" accept=".json,application/json" onchange="handleFileUpload(event)">
                    <label for="fileInput" class="file-input-btn" data-i18n="chooseFile">Choose File</label>
                    <span id="fileNameDisplay" class="file-name" data-i18n="noFileChosen">No file chosen</span>
                </div>
            </div>
        </div>
        
        <div id="errorDiv" class="error-message" style="display: none;"></div>
        
        <div id="results" class="results">
            <div class="issues-section">
                <div class="section-header">
                    <h2 class="section-title" data-i18n="validationResults">Validation Results</h2>
                </div>
                <div id="issuesSummary"></div>
            </div>
            
            <div class="table-section">
                <div class="section-header">
                    <h2 class="section-title" data-i18n="clauseStructure">Clause Structure</h2>
                    <span id="clauseCount"></span>
                </div>
                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th class="col-number" data-i18n="colNumber">Number</th>
                                <th class="col-title" data-i18n="colTitle">Title</th>
                                <th class="col-page" data-i18n="colPage">Page</th>
                                <th class="col-path" data-i18n="colPath">Path</th>
                                <th class="col-content" data-i18n="colContent">Content</th>
                                <th class="col-issues" data-i18n="colIssues">Issues</th>
                            </tr>
                        </thead>
                        <tbody id="clauseTable"></tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Content Modal -->
    <div id="contentModal" class="modal-overlay" onclick="closeModalOnOverlay(event)">
        <div class="modal">
            <div class="modal-header">
                <span class="modal-title" id="modalTitle" data-i18n="modalTitle">Clause Content</span>
                <button class="modal-close" onclick="closeContentModal()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="modal-content-text" id="modalContentText"></div>
            </div>
        </div>
    </div>

    <script>
        const i18n = {
            en: {
                title: 'Clause Structure QA Tool',
                subtitle: 'Validate structural consistency of AI-extracted document clauses',
                inputJson: 'Input JSON',
                analyze: 'Analyze Clauses',
                analyzing: 'Analyzing...',
                clear: 'Clear',
                uploadLabel: 'Or Upload JSON File',
                validationResults: 'Validation Results',
                clauseStructure: 'Clause Structure',
                colNumber: 'Number',
                colTitle: 'Title',
                colPage: 'Page',
                colPath: 'Path',
                colContent: 'Content',
                colIssues: 'Issues',
                modalTitle: 'Clause Content',
                clauses: 'clauses',
                noIssues: 'No structural issues detected',
                continuityGaps: 'Continuity Gaps',
                missingTitles: 'Missing Titles',
                invalidPages: 'Invalid Pages',
                badgeGap: 'Gap',
                badgeNoTitle: 'No Title',
                badgePage: 'Page',
                tooltipNoTitle: 'Missing or empty title',
                tooltipGap: 'Expected {expected} after "{after}", found {found}',
                errorInvalidJson: 'Invalid JSON format. Please check your input.',
                errorEmptyInput: 'Please enter JSON data to analyze.',
                errorNotArray: 'JSON must be an array of clause objects.',
                errorServer: 'Server error: ',
                errorReadFile: 'Error reading file. Please try again.',
                errorInvalidFile: 'Please upload a valid JSON file (.json)',
                noFileChosen: 'No file chosen',
                chooseFile: 'Choose File'
            },
            zh: {
                title: '条款结构QA工具',
                subtitle: '验证AI提取文档条款的结构一致性',
                inputJson: '输入JSON',
                analyze: '分析条款',
                analyzing: '分析中...',
                clear: '清除',
                uploadLabel: '或上传JSON文件',
                validationResults: '验证结果',
                clauseStructure: '条款结构',
                colNumber: '编号',
                colTitle: '标题',
                colPage: '页码',
                colPath: '路径',
                colContent: '内容',
                colIssues: '问题',
                modalTitle: '条款内容',
                clauses: '个条款',
                noIssues: '未检测到结构问题',
                continuityGaps: '连续性缺口',
                missingTitles: '缺失标题',
                invalidPages: '无效页码',
                badgeGap: '缺口',
                badgeNoTitle: '无标题',
                badgePage: '页码',
                tooltipNoTitle: '标题缺失或为空',
                tooltipGap: '在"{after}"之后应为{expected}，实际为{found}',
                errorInvalidJson: 'JSON格式无效，请检查输入。',
                errorEmptyInput: '请输入JSON数据进行分析。',
                errorNotArray: 'JSON必须是条款对象数组。',
                errorServer: '服务器错误：',
                errorReadFile: '读取文件失败，请重试。',
                errorInvalidFile: '请上传有效的JSON文件（.json）',
                noFileChosen: '未选择文件',
                chooseFile: '选择文件'
            }
        };
        
        let currentLang = localStorage.getItem('lang') || 'en';
        
        function t(key, params = {}) {
            let text = i18n[currentLang][key] || i18n['en'][key] || key;
            for (const [k, v] of Object.entries(params)) {
                text = text.replace(`{${k}}`, v);
            }
            return text;
        }
        
        function setLanguage(lang) {
            currentLang = lang;
            localStorage.setItem('lang', lang);
            
            document.getElementById('langEn').classList.toggle('active', lang === 'en');
            document.getElementById('langZh').classList.toggle('active', lang === 'zh');
            
            document.querySelectorAll('[data-i18n]').forEach(el => {
                const key = el.getAttribute('data-i18n');
                el.textContent = t(key);
            });
        }
        
        document.addEventListener('DOMContentLoaded', () => {
            setLanguage(currentLang);
        });
        
        function escapeHtml(text) {
            if (text === null || text === undefined) return '';
            const div = document.createElement('div');
            div.textContent = String(text);
            return div.innerHTML;
        }
        
        function clearInput() {
            document.getElementById('jsonInput').value = '';
            document.getElementById('fileInput').value = '';
            document.getElementById('errorDiv').style.display = 'none';
            document.getElementById('results').style.display = 'none';
            // Reset filename display
            const fileNameDisplay = document.getElementById('fileNameDisplay');
            fileNameDisplay.textContent = t('noFileChosen');
            fileNameDisplay.classList.remove('has-file');
        }
        
        function handleFileUpload(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            // Display selected filename
            const fileNameDisplay = document.getElementById('fileNameDisplay');
            fileNameDisplay.textContent = file.name;
            fileNameDisplay.classList.add('has-file');
            
            // Clear previous results immediately
            document.getElementById('errorDiv').style.display = 'none';
            document.getElementById('results').style.display = 'none';
            
            if (!file.name.endsWith('.json') && file.type !== 'application/json') {
                const errorDiv = document.getElementById('errorDiv');
                errorDiv.textContent = t('errorInvalidFile');
                errorDiv.style.display = 'block';
                event.target.value = '';
                // Reset filename display on invalid file
                fileNameDisplay.textContent = t('noFileChosen');
                fileNameDisplay.classList.remove('has-file');
                return;
            }
            
            const reader = new FileReader();
            reader.onload = function(e) {
                document.getElementById('jsonInput').value = e.target.result;
                // Reset file input to allow re-uploading same file
                document.getElementById('fileInput').value = '';
                analyzeJson();
            };
            reader.onerror = function() {
                const errorDiv = document.getElementById('errorDiv');
                errorDiv.textContent = t('errorReadFile');
                errorDiv.style.display = 'block';
                // Reset file input on error
                document.getElementById('fileInput').value = '';
                // Reset filename display on error
                fileNameDisplay.textContent = t('noFileChosen');
                fileNameDisplay.classList.remove('has-file');
            };
            reader.readAsText(file);
        }
        
        async function analyzeJson() {
            const input = document.getElementById('jsonInput').value.trim();
            const errorDiv = document.getElementById('errorDiv');
            const results = document.getElementById('results');
            const btn = document.getElementById('submitBtn');
            
            errorDiv.style.display = 'none';
            results.style.display = 'none';
            
            if (!input) {
                errorDiv.textContent = t('errorEmptyInput');
                errorDiv.style.display = 'block';
                return;
            }
            
            let parsed;
            try {
                parsed = JSON.parse(input);
            } catch (e) {
                errorDiv.textContent = t('errorInvalidJson');
                errorDiv.style.display = 'block';
                return;
            }
            
            if (!Array.isArray(parsed)) {
                errorDiv.textContent = t('errorNotArray');
                errorDiv.style.display = 'block';
                return;
            }
            
            btn.disabled = true;
            btn.textContent = t('analyzing');
            
            try {
                const response = await fetch('/analyze?t=' + Date.now(), {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Cache-Control': 'no-cache, no-store',
                        'X-Request-Id': Date.now().toString()
                    },
                    body: JSON.stringify({clauses: parsed})
                });
                
                if (!response.ok) {
                    throw new Error(t('errorServer') + response.status);
                }
                
                const data = await response.json();
                renderResults(data);
                results.style.display = 'block';
            } catch (e) {
                errorDiv.textContent = 'Error: ' + e.message;
                errorDiv.style.display = 'block';
            } finally {
                btn.disabled = false;
                btn.textContent = t('analyze');
            }
        }
        
        function renderResults(data) {
            const issuesSummary = document.getElementById('issuesSummary');
            const clauseTable = document.getElementById('clauseTable');
            const clauseCount = document.getElementById('clauseCount');
            const issues = data.issues;
            
            clauseCount.innerHTML = `<span class="badge badge-count">${escapeHtml(data.clauses.length)} ${t('clauses')}</span>`;
            
            // Build issue map by row index
            const issueMap = {};
            
            for (const item of issues.empty_titles) {
                const idx = item.index;
                if (!issueMap[idx]) issueMap[idx] = [];
                issueMap[idx].push({type: 'title', label: t('badgeNoTitle'), tooltip: t('tooltipNoTitle')});
            }
            
            for (const item of issues.invalid_pages) {
                const idx = item.index;
                if (!issueMap[idx]) issueMap[idx] = [];
                issueMap[idx].push({type: 'page', label: t('badgePage'), tooltip: item.reason});
            }
            
            for (const gap of issues.continuity_gaps) {
                // Gap is associated with the "before_clause" row
                const idx = data.clauses.findIndex(c => c.clause_number === gap.before_clause);
                if (idx !== -1) {
                    if (!issueMap[idx]) issueMap[idx] = [];
                    issueMap[idx].push({type: 'gap', label: t('badgeGap'), tooltip: t('tooltipGap', {expected: gap.expected_next, after: gap.after_clause, found: gap.found})});
                }
            }
            
            // Render summary
            const totalIssues = issues.continuity_gaps.length + issues.empty_titles.length + issues.invalid_pages.length;
            let issuesHtml = '';
            
            if (totalIssues === 0) {
                issuesHtml = `<p class="no-issues">${t('noIssues')}</p>`;
            } else {
                issuesHtml = '<div class="issue-summary">';
                if (issues.continuity_gaps.length > 0) {
                    issuesHtml += `<div class="issue-summary-item"><span class="badge badge-warning">${escapeHtml(issues.continuity_gaps.length)}</span> ${t('continuityGaps')}</div>`;
                }
                if (issues.empty_titles.length > 0) {
                    issuesHtml += `<div class="issue-summary-item"><span class="badge badge-warning">${escapeHtml(issues.empty_titles.length)}</span> ${t('missingTitles')}</div>`;
                }
                if (issues.invalid_pages.length > 0) {
                    issuesHtml += `<div class="issue-summary-item"><span class="badge badge-error">${escapeHtml(issues.invalid_pages.length)}</span> ${t('invalidPages')}</div>`;
                }
                issuesHtml += '</div>';
            }
            
            issuesSummary.innerHTML = issuesHtml;
            
            // Render table with inline issue badges
            let tableHtml = '';
            for (let i = 0; i < data.clauses.length; i++) {
                const clause = data.clauses[i];
                const rowIssues = issueMap[i] || [];
                const hasPageError = rowIssues.some(iss => iss.type === 'page');
                const hasAnyIssue = rowIssues.length > 0;
                
                const rowClass = hasPageError ? 'row-issue-error' : (hasAnyIssue ? 'row-issue' : '');
                
                const title = clause.clause_title ? escapeHtml(clause.clause_title) : '<span class="empty-value">—</span>';
                const page = clause.clause_page !== '' && clause.clause_page !== null ? escapeHtml(clause.clause_page) : '<span class="empty-value">—</span>';
                const path = clause.clause_path && clause.clause_path.length > 0 
                    ? `<span class="clause-path">[${clause.clause_path.map(p => escapeHtml(p)).join(', ')}]</span>` 
                    : '<span class="empty-value">—</span>';
                
                let badgesHtml = '';
                if (rowIssues.length > 0) {
                    badgesHtml = '<div class="issue-badges">';
                    for (const iss of rowIssues) {
                        const badgeClass = iss.type === 'gap' ? 'inline-badge-gap' : (iss.type === 'title' ? 'inline-badge-title' : 'inline-badge-page');
                        badgesHtml += `<span class="inline-badge ${badgeClass}" title="${escapeHtml(iss.tooltip)}">${escapeHtml(iss.label)}</span>`;
                    }
                    badgesHtml += '</div>';
                } else {
                    badgesHtml = '<span class="empty-value">—</span>';
                }
                
                // Content preview
                const content = clause.clause_content;
                let contentCell;
                if (content && content.trim()) {
                    const preview = escapeHtml(content.substring(0, 50));
                    contentCell = `<span class="content-preview" onclick="openContentModal(${i})" title="${escapeHtml(content.substring(0, 100))}">${preview}</span>`;
                } else {
                    contentCell = '<span class="content-empty">—</span>';
                }
                
                tableHtml += `<tr class="${rowClass}">
                    <td class="col-number">${clause.clause_number ? escapeHtml(clause.clause_number) : '<span class="empty-value">—</span>'}</td>
                    <td class="col-title">${title}</td>
                    <td class="col-page">${page}</td>
                    <td class="col-path">${path}</td>
                    <td class="col-content">${contentCell}</td>
                    <td class="col-issues">${badgesHtml}</td>
                </tr>`;
            }
            
            clauseTable.innerHTML = tableHtml;
        }
        
        // Store clauses data for modal access
        let currentClausesData = [];
        
        // Override renderResults to store data
        const originalRenderResults = renderResults;
        renderResults = function(data) {
            currentClausesData = data.clauses;
            originalRenderResults(data);
        };
        
        function openContentModal(index) {
            const clause = currentClausesData[index];
            if (!clause || !clause.clause_content) return;
            
            const modal = document.getElementById('contentModal');
            const contentText = document.getElementById('modalContentText');
            const modalTitle = document.getElementById('modalTitle');
            
            modalTitle.textContent = t('modalTitle');
            contentText.textContent = clause.clause_content;
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
        
        function closeContentModal() {
            const modal = document.getElementById('contentModal');
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
        
        function closeModalOnOverlay(event) {
            if (event.target.id === 'contentModal') {
                closeContentModal();
            }
        }
        
        // Close modal on Escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closeContentModal();
            }
        });
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
    
    return JSONResponse(
        content={
            "clauses": display_clauses,
            "issues": issues
        },
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
