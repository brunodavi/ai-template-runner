from unittest import TestCase

from tomllib import loads

from src.ai_template_runner.output import (
    apply_op,
    build_out,
    number_out_headers,
    render_out,
    run_spec,
)


class TestNumberOutHeaders(TestCase):
    def test_numbers_each_name_by_document_order(self):
        numbered = number_out_headers('[[out.strip]]\n[[out.upper]]\n[[out.strip]]\n')

        self.assertEqual(
            numbered,
            '[[out.strip-1]]\n[[out.upper-1]]\n[[out.strip-2]]\n',
        )

    def test_only_out_headers_are_numbered(self):
        toml_str = '[[other.thing]]\n[[out.upper]]\n'

        self.assertEqual(
            number_out_headers(toml_str),
            '[[other.thing]]\n[[out.upper-1]]\n',
        )

    def test_is_idempotent(self):
        toml_str = '[[out.strip]]\n[[out.upper]]\n[[out.strip]]\n'

        once = number_out_headers(toml_str)

        self.assertEqual(number_out_headers(once), once)


class TestBuildOut(TestCase):
    def test_none_stays_empty(self):
        self.assertEqual(build_out(None), {})

    def test_empty_table_stays_empty(self):
        self.assertEqual(build_out({}), {})

    def test_text_only(self):
        built = build_out({'text': '{out.type}: {out.message}'})

        self.assertEqual(built, {'text': '{out.type}: {out.message}'})

    def test_steps_only(self):
        built = build_out({'strip-1': [{}]})

        self.assertEqual(built, {'steps': [('strip', {})]})

    def test_steps_recovered_in_document_order_from_numbered_keys(self):
        raw = loads(number_out_headers(
            '[out]\n'
            "text = 'x'\n"
            '\n'
            '[[out.strip]]\n'
            '\n'
            '[[out.replace]]\n'
            "old = 'GET_health'\n"
            "new = 'GET'\n"
            '\n'
            '[[out.strip]]\n'
            '\n'
            '[[out.upper]]\n'
        ))['out']

        built = build_out(raw)

        self.assertEqual(built['steps'], [
            ('strip', {}),
            ('replace', {'old': 'GET_health', 'new': 'GET'}),
            ('strip', {}),
            ('upper', {}),
        ])

    def test_unknown_keys_become_named_step_args(self):
        raw = loads(number_out_headers(
            '[out]\n'
            '[[out.slice]]\n'
            'start = 1\n'
            'end = 10\n'
        ))['out']

        [step] = build_out(raw)['steps']

        self.assertEqual(step, ('slice', {'start': 1, 'end': 10}))


class TestApplyOp(TestCase):
    def test_empty_args_calls_method_without_arguments(self):
        self.assertEqual(apply_op('  x  ', 'strip', {}), 'x')
        self.assertEqual(apply_op('x', 'upper', {}), 'X')

    def test_named_args_map_to_positional_by_real_signature(self):
        result = apply_op('add GET_health', 'replace', {'old': 'GET_health', 'new': 'GET'})

        self.assertEqual(result, 'add GET')

    def test_unknown_named_arg_fails_descriptively(self):
        with self.assertRaises(ValueError) as ctx:
            apply_op('x', 'replace', {'old': 'a', 'banana': 'b'})

        self.assertIn('banana', str(ctx.exception))

    def test_positional_args_are_used_directly(self):
        result = apply_op('a b c', 'replace', ['b', 'X'])

        self.assertEqual(result, 'a X c')

    def test_slice_with_named_start_end(self):
        self.assertEqual(apply_op('0123456789', 'slice', {'start': 1, 'end': 4}), '123')

    def test_slice_allows_negative_end(self):
        self.assertEqual(apply_op('0123456789', 'slice', {'end': -4}), '012345')

    def test_slice_with_open_end(self):
        self.assertEqual(apply_op('0123456789', 'slice', {'start': 7}), '789')

    def test_slice_with_positional_args(self):
        self.assertEqual(apply_op('0123456789', 'slice', [2, 5]), '234')

    def test_unknown_method_fails_descriptively(self):
        with self.assertRaises(ValueError) as ctx:
            apply_op('x', 'banana', {})

        self.assertIn('banana', str(ctx.exception))

    def test_private_method_fails(self):
        with self.assertRaises(ValueError):
            apply_op('x', '_upper', {})

    def test_non_str_method_is_rejected(self):
        with self.assertRaises(ValueError):
            apply_op('x', 'count', {'sub': 'x'})


class TestRunSpec(TestCase):
    def test_empty_spec_returns_text_unchanged(self):
        self.assertEqual(run_spec('  x  ', ''), '  x  ')

    def test_single_method_without_args(self):
        self.assertEqual(run_spec('  x  ', 'strip'), 'x')

    def test_method_with_positional_args(self):
        self.assertEqual(run_spec('GET_health', 'replace:GET:SET'), 'SET_health')

    def test_slice_spec_with_open_ends(self):
        self.assertEqual(run_spec('0123456789', 'slice:1:4'), '123')
        self.assertEqual(run_spec('0123456789', 'slice:7:'), '789')
        self.assertEqual(run_spec('0123456789', 'slice::4'), '0123')

    def test_unknown_spec_method_fails(self):
        with self.assertRaises(ValueError) as ctx:
            run_spec('x', 'banana')

        self.assertIn('banana', str(ctx.exception))


class TestRenderOut(TestCase):
    def test_no_out_config_returns_raw_response(self):
        self.assertEqual(render_out({}, '{"type": "feat"}'), '{"type": "feat"}')
        self.assertEqual(render_out(None, 'raw'), 'raw')

    def test_text_is_rendered_from_parsed_json_fields(self):
        rendered = render_out(
            {'text': '{out.type}: {out.message}'},
            '{"type": "feat", "message": "add endpoint"}',
        )

        self.assertEqual(rendered, 'feat: add endpoint')

    def test_missing_field_renders_empty(self):
        rendered = render_out(
            {'text': '{out.type}-suffix'},
            '{"message": "x"}',
        )

        self.assertEqual(rendered, '-suffix')

    def test_non_dict_json_renders_empty_fields(self):
        rendered = render_out({'text': '{out.type}'}, '"plain"')

        self.assertEqual(rendered, '')

    def test_invalid_json_renders_empty_fields(self):
        rendered = render_out({'text': '{out.type}'}, 'not json')

        self.assertEqual(rendered, '')

    def test_spec_method_inside_text(self):
        rendered = render_out(
            {'text': '{out.message:strip}'},
            '{"message": "  add endpoint  "}',
        )

        self.assertEqual(rendered, 'add endpoint')

    def test_slice_inside_text(self):
        rendered = render_out(
            {'text': '{out.message[1:4]}'},
            '{"message": "0123456789"}',
        )

        self.assertEqual(rendered, '123')

    def test_json_field_named_like_a_method_is_not_a_transform(self):
        rendered = render_out(
            {'text': '{out.count} {out.title}'},
            '{"count": 3, "title": "Spt"}',
        )

        self.assertEqual(rendered, '3 Spt')

    def test_no_text_applies_steps_to_raw_response(self):
        rendered = render_out({'steps': [('upper', {})]}, 'raw text')

        self.assertEqual(rendered, 'RAW TEXT')

    def test_steps_run_in_document_order_over_rendered_text(self):
        rendered = render_out(
            {
                'text': '{out.type}: {out.message}',
                'steps': [('upper', {}), ('replace', {'old': 'FEAT', 'new': 'FIX'})],
            },
            '{"type": "feat", "message": "add endpoint"}',
        )

        self.assertEqual(rendered, 'FIX: ADD ENDPOINT')

    def test_step_failures_are_descriptive(self):
        with self.assertRaises(ValueError) as ctx:
            render_out({'steps': [('banana', {})]}, 'raw')

        self.assertIn('banana', str(ctx.exception))

    def test_inline_repr_over_json_field(self):
        rendered = render_out(
            {'text': '{out.type!r}'},
            '{"type": "feat"}',
        )

        self.assertEqual(rendered, "'feat'")

    def test_inline_conversion_after_slice(self):
        rendered = render_out(
            {'text': '{out.message[0]!r}'},
            '{"message": "abc"}',
        )

        self.assertEqual(rendered, "'a'")
