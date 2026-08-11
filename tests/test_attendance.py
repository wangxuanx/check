import unittest

from attendance import AttendanceSystem


class AttendanceSystemTests(unittest.TestCase):
    def test_check_in_and_out(self):
        system = AttendanceSystem()
        system.check_in("E001", "2026-08-11", "09:00")
        record = system.check_out("E001", "2026-08-11", "18:00")
        self.assertEqual(record.work_minutes(), 540)

    def test_cannot_checkout_before_checkin(self):
        system = AttendanceSystem()
        with self.assertRaises(ValueError) as context:
            system.check_out("E002", "2026-08-11", "18:00")
        self.assertIn("check in", str(context.exception))

    def test_report_by_date_filters_records(self):
        system = AttendanceSystem()
        system.check_in("E003", "2026-08-11", "08:30")
        system.check_in("E004", "2026-08-12", "08:45")

        rows = system.report_by_date("2026-08-11")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].employee_id, "E003")


if __name__ == "__main__":
    unittest.main()
