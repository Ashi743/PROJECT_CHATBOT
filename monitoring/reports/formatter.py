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
