"""Simple attendance software source code."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime
import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class AttendanceRecord:
    employee_id: str
    work_date: str
    check_in_time: Optional[str] = None
    check_out_time: Optional[str] = None

    def work_minutes(self) -> int:
        if not self.check_in_time or not self.check_out_time:
            return 0
        start = datetime.strptime(self.check_in_time, "%H:%M")
        end = datetime.strptime(self.check_out_time, "%H:%M")
        delta = end - start
        return max(0, int(delta.total_seconds() // 60))


class AttendanceSystem:
    def __init__(self) -> None:
        self._records: Dict[Tuple[str, str], AttendanceRecord] = {}

    def check_in(self, employee_id: str, work_date: str, check_in_time: str) -> AttendanceRecord:
        key = (employee_id, work_date)
        record = self._records.get(key)
        if record and record.check_in_time:
            raise ValueError("Employee already checked in for this date")
        if record is None:
            record = AttendanceRecord(employee_id=employee_id, work_date=work_date)
            self._records[key] = record
        record.check_in_time = check_in_time
        return record

    def check_out(self, employee_id: str, work_date: str, check_out_time: str) -> AttendanceRecord:
        key = (employee_id, work_date)
        record = self._records.get(key)
        if record is None or not record.check_in_time:
            raise ValueError("Employee must check in before check out")
        if record.check_out_time:
            raise ValueError("Employee already checked out for this date")
        record.check_out_time = check_out_time
        return record

    def report_by_date(self, work_date: str) -> List[AttendanceRecord]:
        return [r for r in self._records.values() if r.work_date == work_date]

    def save(self, file_path: str) -> None:
        data = [asdict(record) for record in self._records.values()]
        Path(file_path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def load(self, file_path: str) -> None:
        path = Path(file_path)
        if not path.exists():
            return
        data = json.loads(path.read_text(encoding="utf-8"))
        self._records = {
            (item["employee_id"], item["work_date"]): AttendanceRecord(**item)
            for item in data
        }


def _default_date() -> str:
    return date.today().isoformat()


def _create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Attendance software")
    parser.add_argument("--db", default="attendance.json", help="Path to attendance data file")

    sub = parser.add_subparsers(dest="command", required=True)

    check_in = sub.add_parser("checkin", help="Check in an employee")
    check_in.add_argument("employee_id")
    check_in.add_argument("--date", default=_default_date())
    check_in.add_argument("--time", required=True)

    check_out = sub.add_parser("checkout", help="Check out an employee")
    check_out.add_argument("employee_id")
    check_out.add_argument("--date", default=_default_date())
    check_out.add_argument("--time", required=True)

    report = sub.add_parser("report", help="Show attendance report")
    report.add_argument("--date", default=_default_date())

    return parser


def main() -> None:
    parser = _create_parser()
    args = parser.parse_args()

    system = AttendanceSystem()
    system.load(args.db)

    if args.command == "checkin":
        system.check_in(args.employee_id, args.date, args.time)
        system.save(args.db)
        print("Check-in recorded successfully")
        return

    if args.command == "checkout":
        system.check_out(args.employee_id, args.date, args.time)
        system.save(args.db)
        print("Check-out recorded successfully")
        return

    rows = system.report_by_date(args.date)
    total_minutes = sum(row.work_minutes() for row in rows)
    print(f"records={len(rows)} total_minutes={total_minutes}")


if __name__ == "__main__":
    main()
