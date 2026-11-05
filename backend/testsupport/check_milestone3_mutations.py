"""Run with the test profile. Change rules only in a temporary project copy."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
CASES = [
    ('departure_included', 'backend/app/business/analytics_service.py',
     'min(booking.departure, date(year + 1, 1, 1))',
     'min(booking.departure + timedelta(days=1), date(year + 1, 1, 1))',
     'backend/tests/integration/test_analytics_api.py::test_us7_1_year_boundary'),
    ('cancelled_booking_included', 'backend/app/business/analytics_service.py',
     'if booking.status is ResourceStatus.CANCELLED:', 'if False:',
     'backend/tests/integration/test_analytics_api.py::test_us4_2_cancelled_booking_contributes_nothing'),
    ('cancelled_sale_included', 'backend/app/business/analytics_service.py',
     'sale.status is ResourceStatus.ACTIVE and sale.employee_id', 'sale.employee_id',
     'backend/tests/integration/test_analytics_api.py::test_us9_2_year_employee_and_us6_2_cancelled_excluded'),
    ('guest_count_multiplies_revenue', 'backend/app/business/analytics_service.py',
     'booking.nightly_rate for booking, nights in selected',
     'booking.nightly_rate * booking.guest_count for booking, nights in selected',
     'backend/tests/integration/test_analytics_api.py::test_us7_3_guests_and_revenue'),
    ('no_consistent_snapshot', 'backend/app/data_access/unit_of_work.py',
     'execution_options={"isolation_level": "REPEATABLE READ"}',
     'execution_options={"isolation_level": "READ COMMITTED"}',
     'backend/tests/integration/test_analytics_snapshot.py::test_both_analyses_read_rows_from_their_catalog_snapshot'),
]


def main():
    assert os.environ.get('DATABASE_HOST') == 'test-db'
    with tempfile.TemporaryDirectory(prefix='hotel-milestone3-') as temporary:
        copy = Path(temporary) / 'project'
        shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns('.git', '__pycache__', '.pytest_cache'))
        for name, file, original, replacement, test in CASES:
            path = copy / file
            source = path.read_text()
            assert original in source, name
            path.write_text(source.replace(original, replacement))
            environment = os.environ | {'PYTHONPATH': str(copy / 'backend')}
            result = subprocess.run([sys.executable, '-m', 'pytest', '-q', test], cwd=copy,
                                    env=environment, capture_output=True, text=True)
            path.write_text(source)
            # An import/collection error does not prove that a rule test works.
            if result.returncode != 1 or 'FAILED ' + test not in result.stdout:
                print(result.stdout, result.stderr)
                raise AssertionError(f'{name}: expected a failing assertion, got {result.returncode}')
            print(f'{name}: DETECTED by {test}', flush=True)


if __name__ == '__main__':
    main()
