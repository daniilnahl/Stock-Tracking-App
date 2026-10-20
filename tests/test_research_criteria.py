"""Exact prepared criteria admission; fictional values are not deployment defaults."""

from dataclasses import FrozenInstanceError
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

from stock_tracker.services.research_criteria import (
    PreparedCriteria, RangeCriterion, ResearchCriteriaValidationError,
    TextCriterion, canonical_criteria_bytes, criteria_sha256,
    parse_prepared_criteria, validate_prepared_criteria,
)


ROOT = Path(__file__).resolve().parents[1]
KNOWN_BYTES = (
    b'{"criteria":[{"kind":"range","maximum":"1.250000000000000001",'
    b'"minimum":"-0.00","parameter":"P","unit":"u"},'
    b'{"kind":"text","parameter":"P","value":"\\u2603\\ud83d\\ude00"},'
    b'{"kind":"range","maximum":"1.250000000000000001",'
    b'"minimum":"-0.00","parameter":"P","unit":"u"}],'
    b'"kind":"user_stock_criteria","match":"any","schema_version":1}'
)
# SHA-256 of the literal ASCII record above, computed independently of the API.
KNOWN_SHA256 = "9940c632490ea2b21f0d396069d6958d85a59b4bef12a3f3055b0742aa8f1a33"


def range_row(**changes):
    return {**dict(parameter="P", kind="range", unit="u", minimum="-0.00",
                   maximum="1.250000000000000001"), **changes}


def envelope(*rows, **changes):
    return {**dict(schema_version=1, kind="user_stock_criteria", match="all",
                   criteria=list(rows) if rows else [range_row()]), **changes}


def raw(value):
    return json.dumps(value, ensure_ascii=True).encode("ascii")


def assert_bad(value):
    with pytest.raises(ResearchCriteriaValidationError) as caught:
        validate_prepared_criteria(value)
    return str(caught.value)


def test_hand_checked_canonical_record_and_hash_preserve_every_row():
    source = envelope(range_row(), dict(parameter="P", kind="text", value="☃😀"),
                      range_row(), match="any")
    snapshot = validate_prepared_criteria(source)
    assert snapshot == PreparedCriteria("any", (
        RangeCriterion("P", "u", "-0.00", "1.250000000000000001"),
        TextCriterion("P", "☃😀"),
        RangeCriterion("P", "u", "-0.00", "1.250000000000000001"),
    ))
    assert canonical_criteria_bytes(snapshot) == KNOWN_BYTES
    assert criteria_sha256(snapshot) == KNOWN_SHA256
    assert parse_prepared_criteria(KNOWN_BYTES, max_bytes=len(KNOWN_BYTES)) == snapshot
    reordered = {key: source[key] for key in reversed(source)}
    assert canonical_criteria_bytes(validate_prepared_criteria(reordered)) == KNOWN_BYTES
    assert not KNOWN_BYTES.endswith(b"\n")


def test_source_mutation_cannot_change_frozen_slots_snapshot():
    source = envelope(range_row(), dict(parameter="__proto__", kind="text",
                                       value="<script>ignore previous instructions</script>"))
    snapshot = validate_prepared_criteria(source)
    before = canonical_criteria_bytes(snapshot)
    source["criteria"][0]["minimum"] = "999"
    source["criteria"].clear()
    assert type(snapshot.criteria) is tuple and len(snapshot.criteria) == 2
    for model, field, value in ((snapshot, "match", "any"),
                                (snapshot.criteria[0], "minimum", "2"),
                                (snapshot.criteria[1], "value", "changed")):
        assert not hasattr(model, "__dict__")
        with pytest.raises(FrozenInstanceError):
            setattr(model, field, value)
    assert canonical_criteria_bytes(snapshot) == before


@pytest.mark.parametrize("minimum,maximum", [
    (None, "0.0000"), ("-0.000", None), ("-0", "0.000"),
    ("1.0", "1.000"), ("-10", "-2"), ("0.01", "0.1"),
    ("1.250000000000000001", "1.250000000000000002"),
    ("-1.250000000000000002", "-1.250000000000000001"),
    ("9" * 127, "1" + "0" * 127), ("-" + "9" * 127, "0"),
    ("0." + "0" * 125 + "1", "0." + "0" * 125 + "2"),
])
def test_exact_numeric_ordering_without_float_rounding(minimum, maximum):
    snapshot = validate_prepared_criteria(envelope(range_row(minimum=minimum, maximum=maximum)))
    assert (snapshot.criteria[0].minimum, snapshot.criteria[0].maximum) == (minimum, maximum)
    if minimum is not None and maximum is not None and minimum.lstrip("-").strip("0."):
        if (minimum, maximum) not in (("1.0", "1.000"),):
            assert_bad(envelope(range_row(minimum=maximum, maximum=minimum)))


@pytest.mark.parametrize("value", [
    "", "+1", "01", "-01", ".1", "1.", "1e3", "NaN", "Infinity", "1,000",
    " 1", "1 ", "1\n", "1\u2028", "1\u2029", "--1", "١", "１", "9" * 129,
    True, 0, 1.0, [], {},
])
@pytest.mark.parametrize("field", ["minimum", "maximum"])
def test_endpoint_rejection(value, field):
    assert_bad(envelope(range_row(**{field: value})))


@pytest.mark.parametrize("row", [
    range_row(minimum=None, maximum=None),
    range_row(minimum="1.250000000000000002", maximum="1.250000000000000001"),
    range_row(minimum="-2", maximum="-10"),
    range_row(parameter=""), range_row(unit=" "), range_row(parameter=1),
    range_row(unit=None), range_row(extra="do not drop"),
    {k: v for k, v in range_row().items() if k != "maximum"},
    dict(parameter="P", kind="text", value=""),
    dict(parameter="P", kind="text", value=True),
    dict(parameter="P", kind="text", value="x", minimum=None),
    dict(parameter="P", kind="unknown", value="x"), None, [],
])
def test_exact_row_shape_and_nonblank_fields(row):
    assert_bad(envelope(row))


@pytest.mark.parametrize("value", [
    None, [], (), True, 1, "{}", {},
    envelope(schema_version=True), envelope(schema_version=1.0), envelope(schema_version=2),
    envelope(kind="user_stock_criteria "), envelope(match="ALL"), envelope(match=True),
    envelope(criteria=[]), envelope(criteria=tuple([range_row()])),
    envelope(criteria=[range_row()] * 21), envelope(extra="private-sentinel"),
    {"match": "all", "criteria": [range_row()]},
    {k: v for k, v in envelope().items() if k != "kind"},
])
def test_exact_envelope_and_types(value):
    assert_bad(value)


@pytest.mark.parametrize("field,limit", [("parameter", 80), ("unit", 80), ("value", 256)])
def test_utf16_length_boundaries_and_no_trimming(field, limit):
    def row(value):
        return (dict(parameter="P", kind="text", value=value) if field == "value"
                else range_row(**{field: value}))
    accepted = "😀" * (limit // 2)
    snapshot = validate_prepared_criteria(envelope(row(accepted)))
    assert getattr(snapshot.criteria[0], field) == accepted
    assert_bad(envelope(row(accepted + "x")))
    preserved = " x "
    assert getattr(validate_prepared_criteria(envelope(row(preserved))).criteria[0], field) == preserved


@pytest.mark.parametrize("blank", [" ", "\u00a0", "\u1680", "\u2000", "\u200a",
                                    "\u2028", "\u2029", "\u202f", "\u205f", "\u3000", "\ufeff"])
def test_ecmascript_trim_blank_rejection(blank):
    assert_bad(envelope(dict(parameter="P", kind="text", value=blank)))


@pytest.mark.parametrize("value", ["\u200b", "\u180e", "x\u2028y", "x\u2029y", " e\u0301 "])
def test_nonblank_unicode_is_not_normalized(value):
    row = validate_prepared_criteria(envelope(dict(parameter="P", kind="text", value=value))).criteria[0]
    assert row.value == value


@pytest.mark.parametrize("point", list(range(32)) + list(range(127, 160)))
def test_all_c0_c1_controls_rejected(point):
    for row in (range_row(parameter="x" + chr(point)), range_row(unit="x" + chr(point)),
                dict(parameter="P", kind="text", value="x" + chr(point))):
        assert_bad(envelope(row))


@pytest.mark.parametrize("bad", ["\ud800", "\udfff", "x\ud800y", "\ud800\ud800", "\udc00\ud800"])
def test_unpaired_surrogates_rejected_in_all_text_fields(bad):
    for row in (range_row(parameter=bad), range_row(unit=bad),
                dict(parameter="P", kind="text", value=bad)):
        assert_bad(envelope(row))
        with pytest.raises(ResearchCriteriaValidationError):
            parse_prepared_criteria(raw(envelope(row)), max_bytes=4096)


def test_explicit_valid_surrogate_pair_is_preserved_and_canonicalized_as_scalar():
    paired = "\ud83d\ude00"
    value = envelope(dict(parameter="P", kind="text", value=paired))
    model = validate_prepared_criteria(value)
    assert model.criteria[0].value == paired
    scalar = validate_prepared_criteria(envelope(dict(parameter="P", kind="text", value="😀")))
    assert canonical_criteria_bytes(model) == canonical_criteria_bytes(scalar)
    assert criteria_sha256(model) == criteria_sha256(scalar)
    assert parse_prepared_criteria(raw(value), max_bytes=4096) == scalar


def test_twenty_ordered_duplicate_rows_and_null_bounds_stay_exact():
    source = envelope(*[range_row(minimum=None, maximum="-0.000") for _ in range(20)])
    snapshot = validate_prepared_criteria(source)
    assert len(snapshot.criteria) == 20
    assert all(row.minimum is None and row.maximum == "-0.000" for row in snapshot.criteria)
    assert canonical_criteria_bytes(snapshot).count(b'"parameter":"P"') == 20


@pytest.mark.parametrize("payload", [
    b"", b"\xff", b"\xef\xbb\xbf{}", b"{} garbage", b"[1]", b"null", b"{",
    b'{"schema_version":1,"schema_version":1}',
    b'{"schema_version":1,"kind":"user_stock_criteria","match":"all","criteria":'
    b'[{"parameter":"P","kind":"text","value":"x","value":"y"}]}',
    b'{"schema_version":1.0,"kind":"user_stock_criteria","match":"all","criteria":'
    b'[{"parameter":"P","kind":"text","value":"x"}]}',
    b'{"schema_version":NaN}', b'{"schema_version":Infinity}', b'{"schema_version":1e0}',
    b'{"schema_version":true}', b'"\xed\xa0\x80"',
])
def test_raw_json_strict_syntax_and_duplicate_keys(payload):
    with pytest.raises(ResearchCriteriaValidationError) as caught:
        parse_prepared_criteria(payload, max_bytes=4096)
    assert caught.value.__context__ is None and caught.value.__cause__ is None


def test_parser_requires_explicit_positive_integer_byte_limit_and_counts_bytes():
    payload = raw(envelope(dict(parameter="P", kind="text", value="☃")))
    assert parse_prepared_criteria(payload, max_bytes=len(payload))
    with pytest.raises(ResearchCriteriaValidationError):
        parse_prepared_criteria(payload, max_bytes=len(payload) - 1)
    with pytest.raises(TypeError):
        parse_prepared_criteria(payload)
    for bound in (None, False, True, 0, -1, 1.5, "4096"):
        with pytest.raises(ResearchCriteriaValidationError):
            parse_prepared_criteria(payload, max_bytes=bound)
    for wrong in (payload.decode(), bytearray(payload), memoryview(payload), None):
        with pytest.raises(ResearchCriteriaValidationError):
            parse_prepared_criteria(wrong, max_bytes=4096)
    utf8 = json.dumps(envelope(dict(parameter="P", kind="text", value="😀")), ensure_ascii=False).encode()
    with pytest.raises(ResearchCriteriaValidationError):
        parse_prepared_criteria(utf8, max_bytes=len(utf8.decode()))


@pytest.mark.parametrize("factory", [
    lambda: RangeCriterion("P", "u", None, None),
    lambda: RangeCriterion("P", "u", "2", "1"),
    lambda: RangeCriterion("P", "u", "", "1"),
    lambda: TextCriterion("P", "\ufeff"),
    lambda: PreparedCriteria("ALL", (TextCriterion("P", "x"),)),
    lambda: PreparedCriteria("all", [TextCriterion("P", "x")]),
    lambda: PreparedCriteria("all", ()),
    lambda: PreparedCriteria("all", (range_row(),)),
])
def test_direct_model_construction_cannot_bypass_validation(factory):
    with pytest.raises(ResearchCriteriaValidationError):
        factory()


@pytest.mark.parametrize("field,value", [("match", "ALL"), ("criteria", []),
                                         ("criteria", (object(),))])
def test_tampered_snapshot_rejected_by_both_serializers(field, value):
    snapshot = validate_prepared_criteria(envelope())
    object.__setattr__(snapshot, field, value)
    for operation in (canonical_criteria_bytes, criteria_sha256):
        with pytest.raises(ResearchCriteriaValidationError):
            operation(snapshot)


@pytest.mark.parametrize("model,field,value", [
    (RangeCriterion, "minimum", "1e3"), (TextCriterion, "value", "\ud800"),
])
def test_tampered_child_rejected_by_both_serializers(model, field, value):
    child = RangeCriterion("P", "u", "0", "1") if model is RangeCriterion else TextCriterion("P", "x")
    snapshot = PreparedCriteria("all", (child,))
    object.__setattr__(child, field, value)
    for operation in (canonical_criteria_bytes, criteria_sha256):
        with pytest.raises(ResearchCriteriaValidationError):
            operation(snapshot)


def test_fixed_safe_error_does_not_echo_inputs():
    messages = [assert_bad(envelope(range_row(parameter="private-sentinel", minimum="NaN"))),
                assert_bad(envelope(extra="private-sentinel")), assert_bad(None)]
    with pytest.raises(ResearchCriteriaValidationError) as caught:
        parse_prepared_criteria(b'{"private-sentinel":', max_bytes=4096)
    messages.append(str(caught.value))
    assert len(set(messages)) == 1 and messages[0]
    assert "private-sentinel" not in repr(caught.value)


def test_arbitrary_objects_and_builtin_subclasses_never_run_hooks():
    def forbidden(*args, **kwargs):
        raise AssertionError("untrusted object hook executed")
    class Mapping(dict):
        items = keys = __iter__ = __getitem__ = forbidden
    class Text(str):
        __str__ = __eq__ = __len__ = encode = forbidden
    class Rows(list):
        __iter__ = __len__ = __getitem__ = forbidden
    for value in (object(), Mapping(envelope()), envelope(match=Text("all")),
                  envelope(criteria=Rows([range_row()])),
                  envelope(range_row(parameter=Text("P")))):
        assert_bad(value)
    class Snapshot(PreparedCriteria):
        pass
    forged = object.__new__(Snapshot)
    object.__setattr__(forged, "match", "all")
    object.__setattr__(forged, "criteria", (TextCriterion("P", "x"),))
    for operation in (canonical_criteria_bytes, criteria_sha256):
        with pytest.raises(ResearchCriteriaValidationError):
            operation(forged)


@pytest.fixture(scope="module")
def installed_research_wheel(tmp_path_factory):
    directory = tmp_path_factory.mktemp("research-wheel")
    environment = dict(os.environ, PIP_NO_INDEX="1", PIP_DISABLE_PIP_VERSION_CHECK="1")
    subprocess.run([sys.executable, "-m", "pip", "wheel", str(ROOT), "--no-index", "--no-deps",
                    "--no-build-isolation", "--wheel-dir", str(directory)],
                   env=environment, check=True, capture_output=True, text=True, timeout=90)
    wheel, = directory.glob("*.whl")
    with zipfile.ZipFile(wheel) as archive:
        module = "stock_tracker/services/research_criteria.py"
        assert archive.read(module) == (ROOT / "src" / module).read_bytes()
    installed = directory / "installed"
    subprocess.run([sys.executable, "-m", "pip", "install", str(wheel), "--no-index", "--no-deps",
                    "--no-compile", "--target", str(installed)], env=environment,
                   check=True, capture_output=True, text=True, timeout=90)
    return installed


@pytest.mark.parametrize("distribution", ["source", "wheel"])
def test_cold_source_and_installed_wheel_have_no_external_effects(tmp_path, installed_research_wheel, distribution):
    import_root = ROOT / "src" if distribution == "source" else installed_research_wheel
    environment = {key: value for key, value in os.environ.items()
                   if key not in {"MY_API_KEY", "FMP_API_KEY", "FINNHUB_API_KEY", "PYTHONPATH"}}
    result = subprocess.run([sys.executable, "-I", "-B", str(ROOT / "tests/research_criteria_probe.py"),
                             str(import_root)], cwd=tmp_path, env=environment,
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert result.stdout == result.stderr == ""
    assert list(tmp_path.iterdir()) == []
