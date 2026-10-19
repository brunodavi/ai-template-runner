from unittest import TestCase

from src.ai_template_runner.checks import run_checks


class TestRunChecks(TestCase):
    def test_no_tests_returns_no_results(self):
        results = run_checks({}, '{"type": "feat"}')

        self.assertEqual(results, [])

    def test_json_field_equality_passes(self):
        results = run_checks(
            {'type': 'feat', 'message': 'add endpoint'},
            '{"type": "feat", "message": "add endpoint"}',
        )

        self.assertTrue(all(result.passed for result in results))
        self.assertEqual(
            [result.name for result in results],
            ['type', 'message'],
        )

    def test_json_field_equality_fails(self):
        results = run_checks(
            {'type': 'feat'},
            '{"type": "refactor"}',
        )

        [result] = results
        self.assertFalse(result.passed)
        self.assertIn("expected 'feat'", result.detail)
        self.assertIn("'refactor'", result.detail)

    def test_json_nested_path_with_dotted_key(self):
        results = run_checks(
            {'user.name': 'Alice'},
            '{"user": {"name": "Alice"}}',
        )

        [result] = results
        self.assertTrue(result.passed)

    def test_missing_json_field_fails_without_error(self):
        results = run_checks(
            {'type': 'feat'},
            '{"message": "add endpoint"}',
        )

        [result] = results
        self.assertFalse(result.passed)
        self.assertIn('type', result.detail)

    def test_invalid_json_fails_every_json_check(self):
        results = run_checks(
            {'type': 'feat', 'message': 'x'},
            'not json at all',
        )

        self.assertEqual(len(results), 2)
        self.assertTrue(all(not result.passed for result in results))
        self.assertIn('json', results[0].detail.lower())

    def test_non_string_json_values_are_compared_directly(self):
        results = run_checks(
            {'count': 3, 'active': True, 'tag': None},
            '{"count": 3, "active": true, "tag": null}',
        )

        self.assertTrue(all(result.passed for result in results))

    def test_text_equality_passes_and_fails(self):
        [passed] = run_checks({'text': 'Hello'}, 'Hello')
        [failed] = run_checks({'text': 'Hello'}, 'Hello World')

        self.assertTrue(passed.passed)
        self.assertFalse(failed.passed)

    def test_text_contains_requires_every_fragment(self):
        results = run_checks(
            {'text_contains': ['GET_health', 'feat']},
            'adds a GET_health endpoint: feat',
        )

        [result] = results
        self.assertTrue(result.passed)

        results = run_checks(
            {'text_contains': ['GET_health', 'fix']},
            'adds a GET_health endpoint: feat',
        )

        [result] = results
        self.assertFalse(result.passed)
        self.assertIn('fix', result.detail)

    def test_text_regex_uses_search(self):
        [passed] = run_checks({'text_regex': r'^\{'}, '{"type": "feat"}')
        [failed] = run_checks({'text_regex': r'^\[.'}, '{"type": "feat"}')

        self.assertTrue(passed.passed)
        self.assertFalse(failed.passed)

    def test_invalid_regex_fails_descriptively(self):
        results = run_checks({'text_regex': '^['}, '{"type": "feat"}')

        [result] = results
        self.assertFalse(result.passed)
        self.assertIn('regex', result.detail.lower())

    def test_mixed_reserved_and_json_keys(self):
        results = run_checks(
            {
                'type': 'feat',
                'text_contains': ['feat'],
                'text_regex': r'^\{',
            },
            '{"type": "feat"}',
        )

        self.assertEqual(len(results), 3)
        self.assertTrue(all(result.passed for result in results))

    def test_results_detail_contains_expected_and_got(self):
        results = run_checks({'type': 'feat'}, '{"type": "fix"}')

        [result] = results
        self.assertIn("expected 'feat'", result.detail)
        self.assertIn("got 'fix'", result.detail)
