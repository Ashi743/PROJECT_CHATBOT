from datetime import datetime
import json


def has_issues(results: dict) -> bool:
    for section, items in results.items():
        if isinstance(items, dict):
            for key, value in items.items():
                if isinstance(value, dict) and "status" in value:
                    status = value["status"]
                    if status in ["[ALERT]", "[DOWN]", "[WARN]", "[ERROR]"]:
                        return True
    return False


def format_issue_alert(results: dict) -> str:
    issues = []

    for section, items in results.items():
        if isinstance(items, dict):
            for key, value in items.items():
                if isinstance(value, dict) and "status" in value:
                    status = value["status"]
                    if status in ["[ALERT]", "[DOWN]", "[WARN]", "[ERROR]"]:
                        issue_line = f"[{status}] {key}: {status}"
                        if "error" in value:
                            issue_line += f" - {value['error']}"
                        issues.append(issue_line)

    if not issues:
        return format_all_clear()

    msg = f"""[ALERT] ISSUES DETECTED
Timestamp: {datetime.now().strftime("%d %b %Y %H:%M:%S")}

Issues:
"""
    msg += "\n".join(issues)
    msg += "\n\nCheck chatbot for full report"

    return _truncate_to_slack_limit(msg)


def format_daily_report(results: dict) -> str:
    msg = f"""DAILY SYSTEM REPORT
Timestamp: {datetime.now().strftime("%d %b %Y %H:%M:%S")}
================================

"""

    if has_issues(results):
        msg += "ISSUES DETECTED:\n"
        for section, items in results.items():
            if isinstance(items, dict):
                for key, value in items.items():
                    if isinstance(value, dict) and "status" in value:
                        if value["status"] in ["[ALERT]", "[DOWN]", "[WARN]", "[ERROR]"]:
                            msg += f"  {value['status']} {key}\n"
        msg += "\n"

    msg += "COMMODITIES:\n"
    if "commodities" in results:
        for commodity, data in results["commodities"].items():
            if isinstance(data, dict):
                status = data.get("status", "[UNKNOWN]")
                change = data.get("change", "N/A")
                msg += f"  {commodity.upper():<10} {status:<8} Change: {change:>7}%\n"
    msg += "\n"

    msg += "APIs:\n"
    if "apis" in results:
        for api, data in results["apis"].items():
            if isinstance(data, dict):
                status = data.get("status", "[UNKNOWN]")
                response_ms = data.get("response_ms", "N/A")
                msg += f"  {api:<20} {status:<8} Response: {response_ms} ms\n"
    msg += "\n"

    msg += "FILES:\n"
    if "files" in results:
        file_issues = 0
        for file, data in results["files"].items():
            if isinstance(data, dict):
                status = data.get("status", "[OK]")
                if status != "[OK]":
                    file_issues += 1
                    msg += f"  {file:<30} {status}\n"
        if file_issues == 0:
            msg += "  All files [OK]\n"
    msg += "\n"

    msg += "DATABASES:\n"
    if "databases" in results:
        if not results["databases"]:
            msg += "  No databases found\n"
        else:
            for db, data in results["databases"].items():
                if isinstance(data, dict):
                    status = data.get("status", "[UNKNOWN]")
                    size_mb = data.get("size_mb", "N/A")
                    rows = data.get("rows", "N/A")
                    msg += f"  {db:<20} {status:<8} Size: {size_mb} MB, Rows: {rows}\n"
    msg += "\n"

    msg += "CHROMADB:\n"
    if "chromadb" in results:
        chroma = results["chromadb"].get("chromadb", {})
        status = chroma.get("status", "[UNKNOWN]")
        docs = chroma.get("documents", 0)
        disk = chroma.get("disk_mb", 0)
        msg += f"  Status: {status}  Documents: {docs}  Disk: {disk} MB\n"
    msg += "\n"

    msg += "APP HEALTH:\n"
    if "app" in results:
        app = results["app"].get("app_health", {})
        status = app.get("status", "[UNKNOWN]")
        memory = app.get("memory_pct", "N/A")
        cpu = app.get("cpu_pct", "N/A")
        disk = app.get("disk_pct", "N/A")
        msg += f"  Status: {status}  Memory: {memory}%  CPU: {cpu}%  Disk: {disk}%\n"

    msg += "\n================================"

    return _truncate_to_slack_limit(msg)


def format_all_clear() -> str:
    return f"All systems [OK] - {datetime.now().strftime('%d %b %Y %H:%M:%S')}"


def _truncate_to_slack_limit(msg: str, limit: int = 4000) -> str:
    if len(msg) > limit:
        return msg[:limit - 3] + "..."
    return msg


def format_report_as_html(results: dict) -> str:
    """Format report as HTML table for email."""
    html = f"""<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
        th {{ background-color: #2c3e50; color: white; padding: 10px; text-align: left; border: 1px solid #ddd; }}
        td {{ padding: 8px; border: 1px solid #ddd; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .alert {{ background-color: #ffe6e6; }}
        .down {{ background-color: #ffcccc; }}
        .warn {{ background-color: #fff9e6; }}
        .ok {{ background-color: #e6ffe6; }}
        .section-title {{ font-size: 16px; font-weight: bold; margin-top: 20px; margin-bottom: 10px; color: #2c3e50; }}
        .timestamp {{ color: #666; font-size: 12px; }}
    </style>
</head>
<body>
<h2>DAILY SYSTEM REPORT</h2>
<p class="timestamp">Timestamp: {datetime.now().strftime("%d %b %Y %H:%M:%S")}</p>
"""

    if has_issues(results):
        html += '<div class="section-title">Issues Detected</div>'
        html += '<table><tr><th>Component</th><th>Status</th><th>Details</th></tr>'
        for section, items in results.items():
            if isinstance(items, dict):
                for key, value in items.items():
                    if isinstance(value, dict) and "status" in value:
                        status = value["status"]
                        if status in ["[ALERT]", "[DOWN]", "[WARN]", "[ERROR]"]:
                            css_class = "alert" if status == "[ALERT]" else ("down" if status == "[DOWN]" else "warn")
                            details = value.get("error", "")
                            html += f'<tr class="{css_class}"><td>{key}</td><td>{status}</td><td>{details}</td></tr>'
        html += '</table>'

    if "commodities" in results and results["commodities"]:
        html += '<div class="section-title">Commodities</div>'
        html += '<table><tr><th>Commodity</th><th>Status</th><th>Change %</th></tr>'
        for commodity, data in results["commodities"].items():
            if isinstance(data, dict):
                status = data.get("status", "[UNKNOWN]")
                change = data.get("change", "N/A")
                css_class = "ok" if status == "[OK]" else "warn"
                html += f'<tr class="{css_class}"><td>{commodity.upper()}</td><td>{status}</td><td>{change}</td></tr>'
        html += '</table>'

    if "apis" in results and results["apis"]:
        html += '<div class="section-title">APIs</div>'
        html += '<table><tr><th>API</th><th>Status</th><th>Response (ms)</th></tr>'
        for api, data in results["apis"].items():
            if isinstance(data, dict):
                status = data.get("status", "[UNKNOWN]")
                response = data.get("response_ms", "N/A")
                css_class = "ok" if status == "[OK]" else "down"
                html += f'<tr class="{css_class}"><td>{api}</td><td>{status}</td><td>{response}</td></tr>'
        html += '</table>'

    if "files" in results and results["files"]:
        html += '<div class="section-title">Files</div>'
        html += '<table><tr><th>File</th><th>Status</th></tr>'
        for file, data in results["files"].items():
            if isinstance(data, dict):
                status = data.get("status", "[OK]")
                css_class = "ok" if status == "[OK]" else "alert"
                html += f'<tr class="{css_class}"><td>{file}</td><td>{status}</td></tr>'
        html += '</table>'

    if "databases" in results and results["databases"]:
        html += '<div class="section-title">Databases</div>'
        html += '<table><tr><th>Database</th><th>Status</th><th>Size (MB)</th><th>Rows</th></tr>'
        for db, data in results["databases"].items():
            if isinstance(data, dict):
                status = data.get("status", "[UNKNOWN]")
                size = data.get("size_mb", "N/A")
                rows = data.get("rows", "N/A")
                css_class = "ok" if status == "[OK]" else "warn"
                html += f'<tr class="{css_class}"><td>{db}</td><td>{status}</td><td>{size}</td><td>{rows}</td></tr>'
        html += '</table>'

    if "chromadb" in results:
        chroma = results["chromadb"].get("chromadb", {})
        if chroma:
            html += '<div class="section-title">ChromaDB</div>'
            html += '<table><tr><th>Component</th><th>Status</th><th>Documents</th><th>Disk (MB)</th></tr>'
            status = chroma.get("status", "[UNKNOWN]")
            docs = chroma.get("documents", 0)
            disk = chroma.get("disk_mb", 0)
            css_class = "ok" if status == "[OK]" else "warn"
            html += f'<tr class="{css_class}"><td>ChromaDB</td><td>{status}</td><td>{docs}</td><td>{disk}</td></tr>'
            html += '</table>'

    if "app" in results:
        app = results["app"].get("app_health", {})
        if app:
            html += '<div class="section-title">App Health</div>'
            html += '<table><tr><th>Component</th><th>Status</th><th>Memory %</th><th>CPU %</th><th>Disk %</th></tr>'
            status = app.get("status", "[UNKNOWN]")
            memory = app.get("memory_pct", "N/A")
            cpu = app.get("cpu_pct", "N/A")
            disk = app.get("disk_pct", "N/A")
            css_class = "ok" if status == "[OK]" else "warn"
            html += f'<tr class="{css_class}"><td>App Health</td><td>{status}</td><td>{memory}</td><td>{cpu}</td><td>{disk}</td></tr>'
            html += '</table>'

    html += """
</body>
</html>"""
    return html


def format_report_for_slack(results: dict) -> str:
    """Format report as markdown tables for Slack."""
    msg = f"""*DAILY SYSTEM REPORT*
_Timestamp: {datetime.now().strftime("%d %b %Y %H:%M:%S")}_

"""

    if has_issues(results):
        msg += "*[ALERT] Issues Detected*\n```\n"
        msg += "Component                     Status      Details\n"
        msg += "-" * 70 + "\n"
        for section, items in results.items():
            if isinstance(items, dict):
                for key, value in items.items():
                    if isinstance(value, dict) and "status" in value:
                        if value["status"] in ["[ALERT]", "[DOWN]", "[WARN]", "[ERROR]"]:
                            status = value["status"]
                            error = value.get("error", "")[:30]
                            msg += f"{key:<30} {status:<12} {error}\n"
        msg += "```\n\n"

    if "commodities" in results and results["commodities"]:
        msg += "*Commodities*\n```\n"
        msg += "Commodity              Status      Change %\n"
        msg += "-" * 50 + "\n"
        for commodity, data in results["commodities"].items():
            if isinstance(data, dict):
                status = data.get("status", "[UNKNOWN]")
                change = data.get("change", "N/A")
                msg += f"{commodity.upper():<20} {status:<12} {str(change):>8}\n"
        msg += "```\n\n"

    if "apis" in results and results["apis"]:
        msg += "*APIs*\n```\n"
        msg += "API                      Status      Response (ms)\n"
        msg += "-" * 55 + "\n"
        for api, data in results["apis"].items():
            if isinstance(data, dict):
                status = data.get("status", "[UNKNOWN]")
                response = data.get("response_ms", "N/A")
                msg += f"{api:<25} {status:<12} {str(response):>10}\n"
        msg += "```\n\n"

    if "files" in results and results["files"]:
        issues = [f for f, d in results["files"].items() if isinstance(d, dict) and d.get("status") != "[OK]"]
        if issues:
            msg += "*Files (Issues)*\n```\n"
            msg += "File                             Status\n"
            msg += "-" * 45 + "\n"
            for file in issues:
                data = results["files"][file]
                status = data.get("status", "[UNKNOWN]")
                msg += f"{file:<35} {status}\n"
            msg += "```\n\n"
        else:
            msg += "*Files* - All files [OK]\n\n"

    if "databases" in results and results["databases"]:
        msg += "*Databases*\n```\n"
        msg += "Database                 Status      Size (MB)   Rows\n"
        msg += "-" * 60 + "\n"
        for db, data in results["databases"].items():
            if isinstance(data, dict):
                status = data.get("status", "[UNKNOWN]")
                size = data.get("size_mb", "N/A")
                rows = data.get("rows", "N/A")
                msg += f"{db:<25} {status:<12} {str(size):>10} {str(rows):>8}\n"
        msg += "```\n\n"

    if "chromadb" in results:
        chroma = results["chromadb"].get("chromadb", {})
        if chroma:
            msg += "*ChromaDB*\n```\n"
            msg += "Status           Documents    Disk (MB)\n"
            msg += "-" * 40 + "\n"
            status = chroma.get("status", "[UNKNOWN]")
            docs = chroma.get("documents", 0)
            disk = chroma.get("disk_mb", 0)
            msg += f"{status:<17} {str(docs):>10} {str(disk):>12}\n"
            msg += "```\n\n"

    if "app" in results:
        app = results["app"].get("app_health", {})
        if app:
            msg += "*App Health*\n```\n"
            msg += "Status           Memory %   CPU %     Disk %\n"
            msg += "-" * 45 + "\n"
            status = app.get("status", "[UNKNOWN]")
            memory = app.get("memory_pct", "N/A")
            cpu = app.get("cpu_pct", "N/A")
            disk = app.get("disk_pct", "N/A")
            msg += f"{status:<17} {str(memory):>8} {str(cpu):>8} {str(disk):>7}\n"
            msg += "```\n"

    return _truncate_to_slack_limit(msg)


def get_report_table_data(results: dict) -> dict:
    """Convert report results to structured format for table display."""
    tables = {}

    if "commodities" in results and results["commodities"]:
        commodities_data = []
        for commodity, data in results["commodities"].items():
            if isinstance(data, dict):
                commodities_data.append({
                    "Commodity": commodity.upper(),
                    "Status": data.get("status", "[UNKNOWN]"),
                    "Change %": data.get("change", "N/A")
                })
        if commodities_data:
            tables["Commodities"] = commodities_data

    if "apis" in results and results["apis"]:
        apis_data = []
        for api, data in results["apis"].items():
            if isinstance(data, dict):
                apis_data.append({
                    "API": api,
                    "Status": data.get("status", "[UNKNOWN]"),
                    "Response (ms)": data.get("response_ms", "N/A")
                })
        if apis_data:
            tables["APIs"] = apis_data

    if "files" in results and results["files"]:
        files_data = []
        for file, data in results["files"].items():
            if isinstance(data, dict):
                status = data.get("status", "[OK]")
                if status != "[OK]":
                    files_data.append({
                        "File": file,
                        "Status": status
                    })
        if files_data:
            tables["Files (Issues)"] = files_data

    if "databases" in results and results["databases"]:
        databases_data = []
        for db, data in results["databases"].items():
            if isinstance(data, dict):
                databases_data.append({
                    "Database": db,
                    "Status": data.get("status", "[UNKNOWN]"),
                    "Size (MB)": data.get("size_mb", "N/A"),
                    "Rows": data.get("rows", "N/A")
                })
        if databases_data:
            tables["Databases"] = databases_data

    if "chromadb" in results:
        chroma = results["chromadb"].get("chromadb", {})
        if chroma:
            chroma_data = [{
                "Component": "ChromaDB",
                "Status": chroma.get("status", "[UNKNOWN]"),
                "Documents": chroma.get("documents", 0),
                "Disk (MB)": chroma.get("disk_mb", 0)
            }]
            tables["ChromaDB"] = chroma_data

    if "app" in results:
        app = results["app"].get("app_health", {})
        if app:
            app_data = [{
                "Component": "App Health",
                "Status": app.get("status", "[UNKNOWN]"),
                "Memory %": app.get("memory_pct", "N/A"),
                "CPU %": app.get("cpu_pct", "N/A"),
                "Disk %": app.get("disk_pct", "N/A")
            }]
            tables["App Health"] = app_data

    return tables


if __name__ == "__main__":
    sample_results = {
        "commodities": {
            "wheat": {"price": 543.20, "change": -0.8, "status": "[OK]", "volume": 12400},
            "corn": {"price": 456.10, "change": -2.0, "status": "[ALERT]", "volume": 9800}
        },
        "apis": {
            "DuckDuckGo": {"status": "[OK]", "response_ms": 234},
            "yfinance": {"status": "[DOWN]", "response_ms": None}
        }
    }

    print("Issue Alert:")
    print(format_issue_alert(sample_results))
    print("\n" + "=" * 50 + "\n")

    print("Daily Report:")
    print(format_daily_report(sample_results))
