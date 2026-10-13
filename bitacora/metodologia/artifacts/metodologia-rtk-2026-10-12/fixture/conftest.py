from pathlib import Path

def pytest_sessionfinish(session, exitstatus):
    with (Path(__file__).parent / 'executions.log').open('a') as f:
        f.write(f'{exitstatus}\n')
