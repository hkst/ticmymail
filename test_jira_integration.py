import json
import sys
sys.path.insert(0, 'src')

from tmm.api.http_app import app
from tmm.logger import get_run_log_path, log_error
from tmm.service.phase1_runner import Phase1BatchRunner


def main() -> int:
    with open('src/tmm/tests/email_payload_good.json', 'r', encoding='utf-8') as file_handle:
        payload = json.load(file_handle)

    try:
        print('Phase-1 Jira run start')
        runner = Phase1BatchRunner(app, payload)
        summary = runner.run()
        print('Phase-1 Jira run end')
        print(json.dumps(summary, indent=2))
        return 0
    except Exception as exc:
        log_error('Phase-1 Jira runner failed', error_code='RUNNER_FAILED', details={'error': str(exc)})
        print('Phase-1 Jira run error')
        print(get_run_log_path())
        return 1


if __name__ == '__main__':
    raise SystemExit(main())

