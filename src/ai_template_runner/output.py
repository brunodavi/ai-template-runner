"""The [out] table: render of the AI response with transforms.

Two mechanisms share one transform executor:

- [[out.<method>]] tables build a pipeline applied in real document
  order (array-of-tables group by key in tomllib, so the raw headers
  are numbered with a suffix before parsing and un-numbered after);
- inline spec inside the render text: `{out.field:method:arg1:arg2}`
  and the pythonic slice `{out.field[1:]}` through a Smart wrapper.
"""

import inspect
import json
import re
from tomllib import loads as toml_loads


OUT_HEADER = re.compile(r'\[\[out\.(\w+)\]\]')

SLICE_METHOD = 'slice'
TEXT_KEY = 'text'
STEPS_KEY = 'steps'


def number_out_headers(toml_str: str) -> str:
    """Number [[out.<name>]] headers so document order survives tomllib.

    tomllib groups array-of-tables by key, losing the order between
    different method names. Adding a per-name occurrence suffix gives
    every header a unique key; build_out() removes the suffix again.
    The suffix is not matched by the pattern itself (\w stops at '-'),
    so numbering stays idempotent.
    """
    counters: dict[str, int] = {}

    def rename(match: re.Match) -> str:
        name = match.group(1)
        counters[name] = counters.get(name, 0) + 1
        return f'[[out.{name}-{counters[name]}]]'

    return OUT_HEADER.sub(rename, toml_str)


def build_out(raw_out: dict | None) -> dict:
    """Canonicalize the parsed [out] table into {text, steps}.

    Numbered keys (built with number_out_headers) are un-suffixed and
    flattened into an ordered steps list of (method, args) tuples,
    where args is the step table (empty table = no arguments).
    """
    if not raw_out:
        return {}

    built = {}

    if raw_out.get(TEXT_KEY):
        built[TEXT_KEY] = raw_out[TEXT_KEY]

    steps = []
    for key, entries in raw_out.items():
        if key == TEXT_KEY:
            continue
        method = key.rsplit('-', 1)[0]
        for entry in entries:
            steps.append((method, dict(entry)))

    if steps:
        built[STEPS_KEY] = steps

    return built


def _positional_by_signature(method, args: dict, name: str) -> list:
    """Map named args to positional order using the method's real signature."""
    try:
        params = [
            param
            for param in inspect.signature(method).parameters
            if param != 'self'
        ]
    except (ValueError, TypeError):
        raise ValueError(
            f'[out] cannot map named arguments for transform {name!r}'
        ) from None

    unknown = set(args) - set(params)
    if unknown:
        raise ValueError(
            f'[out] unknown arguments for {name}: {sorted(unknown)}'
        )

    return [args[param] for param in params if param in args]


def _slice_key(args) -> slice:
    if isinstance(args, dict):
        return slice(args.get('start'), args.get('end'))

    start = args[0] if len(args) > 0 else None
    end = args[1] if len(args) > 1 else None
    return slice(
        int(start) if start not in (None, '') else None,
        int(end) if end not in (None, '') else None,
    )


def apply_op(text: str, name: str, args) -> str:
    """Run one transform: a real str method, or the 'slice' helper.

    args is a named dict (from [[out.<method>]] tables, mapped to
    positional by the method signature) or a positional list (from an
    inline spec). An empty args table calls the method without args.
    """
    if name == SLICE_METHOD:
        return text[_slice_key(args)]

    if not hasattr(str, name) or name.startswith('_'):
        raise ValueError(f'[out] unknown transform: {name!r}')

    method = getattr(str, name)

    if not args:
        return method(text)

    if isinstance(args, dict):
        args = _positional_by_signature(method, args, name)

    return method(text, *args)


def run_spec(text: str, spec: str) -> str:
    """Run the inline spec: 'method' | 'method:arg1:arg2' | 'slice:1:10'.

    One step only, positional args separated by ':' (values may not
    contain ':'). An empty spec is a pass-through.
    """
    if not spec:
        return text

    name, *args = spec.split(':')
    return apply_op(text, name, args)


def parse_slice_key(key: str) -> slice:
    """Parse a format subscript key like '1:', ':4' or '1:10' into a slice."""
    start, _, end = key.partition(':')
    return slice(
        int(start) if start else None,
        int(end) if end else None,
    )


class Smart(str):
    """Interpolable value: transforms only via :spec and [slice].

    The format machinery passes subscript keys as strings to
    __getitem__ ('1:' -> slice) and the format spec to __format__
    ('replace:GET:SET'), where we run them through apply_op. Because
    transforms never use attribute names, JSON fields keep their own
    namespace (a field called 'count' is data, never str.count).
    """

    def __getitem__(self, key):
        if isinstance(key, str):
            key = parse_slice_key(key)
        return Smart(super().__getitem__(key))

    def __format__(self, spec: str) -> str:
        return run_spec(str(self), spec)


class Rec:
    """Wraps the parsed JSON response so {out.*} resolves to fields.

    Missing fields render as ''; nested dicts may be addressed with
    dotted attribute access. Values are Smart, so :spec and [slice]
    work on any field.
    """

    def __init__(self, fields: dict):
        object.__setattr__(self, '_fields', fields or {})

    def __getattr__(self, field: str):
        if field.startswith('_'):
            raise AttributeError(field)

        if field not in self._fields:
            return Smart('')

        value = self._fields[field]
        return Rec(value) if isinstance(value, dict) else Smart(value)


def _response_fields(ai_response: str) -> dict:
    try:
        parsed = json.loads(ai_response)
    except (json.JSONDecodeError, TypeError):
        return {}

    return parsed if isinstance(parsed, dict) else {}


def render_out(out: dict | None, ai_response: str) -> str:
    """Render the AI response through the [out] config.

    Without [out] (or an empty table) the raw response passes through.
    With 'text', the parsed JSON fields are formatted through Rec and
    Smart; without 'text' the raw response is the starting value. The
    steps from [[out.<method>]] tables are applied in document order.
    """
    if not out:
        return ai_response

    base = out.get(TEXT_KEY) or ai_response
    if base is not ai_response:
        base = base.format(out=Rec(_response_fields(ai_response)))

    for name, args in out.get(STEPS_KEY, []):
        base = apply_op(base, name, args)

    return base
