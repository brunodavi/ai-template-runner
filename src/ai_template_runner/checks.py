import json
import re


class CheckResult:
    def __init__(self, name: str, passed: bool, detail: str = ''):
        self.name = name
        self.passed = passed
        self.detail = detail


TEXT_KEY = 'text'
TEXT_CONTAINS_KEY = 'text_contains'
TEXT_REGEX_KEY = 'text_regex'


def _quoted(value) -> str:
    return f'{value!r}'


def _json_get(data: dict, dotted_path: str):
    current = data
    for part in dotted_path.split('.'):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def run_checks(test_config: dict, text: str) -> list[CheckResult]:
    """Validate the AI response against the template [test] table.

    Reserved keys (text, text_contains, text_regex) check the raw
    text; any other key is a dotted path into the parsed JSON output.
    Missing JSON fields and invalid JSON fail without raising.
    """
    results: list[CheckResult] = []

    expected_json = {
        key: value
        for key, value in test_config.items()
        if key not in (TEXT_KEY, TEXT_CONTAINS_KEY, TEXT_REGEX_KEY)
    }

    try:
        parsed = json.loads(text)
        parse_error = None
    except (json.JSONDecodeError, TypeError) as err:
        parsed = None
        parse_error = err

    for key, expected in expected_json.items():
        if parse_error is not None:
            results.append(CheckResult(
                key,
                passed=False,
                detail=f'invalid json output: {text[:100]!r}',
            ))
            continue

        got = _json_get(parsed, key)
        passed = got == expected
        detail = '' if passed else (
            f'{key}: expected {_quoted(expected)}, got {_quoted(got)}'
        )
        results.append(CheckResult(key, passed, detail))

    if TEXT_KEY in test_config:
        expected = test_config[TEXT_KEY]
        passed = text == expected
        detail = '' if passed else f'expected {_quoted(expected)}, got {_quoted(text)}'
        results.append(CheckResult(TEXT_KEY, passed, detail))

    if TEXT_CONTAINS_KEY in test_config:
        fragments = test_config[TEXT_CONTAINS_KEY]
        missing = [
            fragment for fragment in fragments
            if fragment not in text
        ]
        passed = not missing
        detail = '' if passed else f'missing fragments: {_quoted(missing)}'
        results.append(CheckResult(TEXT_CONTAINS_KEY, passed, detail))

    if TEXT_REGEX_KEY in test_config:
        pattern = test_config[TEXT_REGEX_KEY]
        try:
            passed = re.search(pattern, text) is not None
            detail = '' if passed else f'pattern {_quoted(pattern)} not found'
        except re.error as err:
            passed = False
            detail = f'invalid regex {_quoted(pattern)}: {err}'
        results.append(CheckResult(TEXT_REGEX_KEY, passed, detail))

    return results
