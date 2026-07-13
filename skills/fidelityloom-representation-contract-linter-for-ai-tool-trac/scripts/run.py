#!/usr/bin/env python3
"""Audit representation fidelity across source, tool-call, and tool-result JSONL stages."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from decimal import Decimal, InvalidOperation, ROUND_DOWN
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


SCHEMA_VERSION = "1.0"
SAFE_INTEGER_MAX = 9_007_199_254_740_991
MISSING = object()
SEVERITY_RANK = {"none": 0, "info": 1, "warning": 2, "error": 3}
PATH_KEYS = {
    "source_path",
    "tool_path",
    "result_path",
    "source_unit_path",
    "tool_unit_path",
    "result_unit_path",
    "source_axes_path",
    "tool_axes_path",
    "result_axes_path",
    "source_dimensions_path",
    "tool_dimensions_path",
    "result_dimensions_path",
}
ALLOWED_FIELD_KEYS = PATH_KEYS | {
    "required",
    "unit",
    "dimensions",
    "nullable",
    "precision",
    "coercion",
    "missing_values",
}
COERCIONS = {"any", "array", "boolean", "integer", "number", "object", "string"}
JSON_SCHEMA_EXTENSIONS = {
    "x-source-path": "source_path",
    "x-tool-path": "tool_path",
    "x-result-path": "result_path",
    "x-source-unit-path": "source_unit_path",
    "x-tool-unit-path": "tool_unit_path",
    "x-result-unit-path": "result_unit_path",
    "x-source-axes-path": "source_axes_path",
    "x-tool-axes-path": "tool_axes_path",
    "x-result-axes-path": "result_axes_path",
    "x-source-dimensions-path": "source_dimensions_path",
    "x-tool-dimensions-path": "tool_dimensions_path",
    "x-result-dimensions-path": "result_dimensions_path",
    "x-unit": "unit",
    "x-dimensions": "dimensions",
    "x-precision": "precision",
    "x-missing-values": "missing_values",
}


SAMPLE_TRACES = [
    {
        "trace_id": "weather-array-001",
        "source": {
            "temperature": {"value": 21.375, "unit": "C"},
            "signal": {
                "axes": ["time", "channel"],
                "shape": [2, 2],
                "values": [[1.0, None], [3.0, 4.0]],
            },
            "sample_id": 9_007_199_254_740_993,
            "missing_reading": None,
        },
        "tool_args": {
            "temperature": {"value": 21.4},
            "signal": {
                "axes": ["channel", "time"],
                "shape": [4],
                "values": [1.0, 0, 3.0, 4.0],
            },
            "sample_id": 9_007_199_254_740_993,
            "missing_reading": 0,
        },
        "tool_result": {
            "temperature": {"value": "21.4", "unit": "C"},
            "signal": {
                "axes": ["channel", "time"],
                "shape": [4],
                "values": [1.0, 0, 3.0, 4.0],
            },
            "sample_id": "9007199254740993",
            "missing_reading": 0,
        },
    }
]

SAMPLE_CONTRACT = {
    "version": 1,
    "fields": {
        "missing_reading": {
            "source_path": "missing_reading",
            "tool_path": "missing_reading",
            "result_path": "missing_reading",
            "required": True,
            "nullable": True,
            "coercion": "number",
            "missing_values": [None, -9999, "NaN"],
        },
        "sample_id": {
            "source_path": "sample_id",
            "tool_path": "sample_id",
            "result_path": "sample_id",
            "required": True,
            "nullable": False,
            "precision": 16,
            "coercion": "integer",
        },
        "signal": {
            "source_path": "signal.values",
            "tool_path": "signal.values",
            "result_path": "signal.values",
            "source_axes_path": "signal.axes",
            "tool_axes_path": "signal.axes",
            "result_axes_path": "signal.axes",
            "source_dimensions_path": "signal.shape",
            "tool_dimensions_path": "signal.shape",
            "result_dimensions_path": "signal.shape",
            "required": True,
            "dimensions": ["time", "channel"],
            "nullable": True,
            "coercion": "array",
            "missing_values": [None, -9999, "NaN"],
        },
        "temperature": {
            "source_path": "temperature.value",
            "tool_path": "temperature.value",
            "result_path": "temperature.value",
            "source_unit_path": "temperature.unit",
            "tool_unit_path": "temperature.unit",
            "result_unit_path": "temperature.unit",
            "required": True,
            "unit": "C",
            "nullable": False,
            "precision": 5,
            "coercion": "number",
        },
    },
}


class FidelityError(ValueError):
    """Raised when input traces or contracts violate the public input contract."""


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    """Load a UTF-8 JSONL file and return validated raw record objects."""

    records: list[dict[str, Any]] = []
    file_path = Path(path)
    try:
        lines = file_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise FidelityError(f"cannot read trace file '{file_path}': {exc}") from exc
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise FidelityError(
                f"invalid JSON in '{file_path}' at line {line_number}, column {exc.colno}: {exc.msg}"
            ) from exc
        if not isinstance(value, dict):
            raise FidelityError(f"trace line {line_number} must be a JSON object")
        records.append(value)
    if not records:
        raise FidelityError(f"trace file '{file_path}' contains no JSON records")
    return records


def load_contract(path: str | Path) -> dict[str, Any]:
    """Load a JSON representation contract from disk."""

    file_path = Path(path)
    try:
        value = json.loads(file_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise FidelityError(f"cannot read contract file '{file_path}': {exc}") from exc
    except json.JSONDecodeError as exc:
        raise FidelityError(
            f"invalid JSON in contract '{file_path}' at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc
    if not isinstance(value, dict):
        raise FidelityError("contract root must be a JSON object")
    return value


def validate_traces(traces: Sequence[Mapping[str, Any]]) -> None:
    """Validate the three-stage trace structure before analysis."""

    if not isinstance(traces, Sequence) or isinstance(traces, (str, bytes)) or not traces:
        raise FidelityError("traces must be a non-empty sequence")
    seen_ids: set[str] = set()
    for index, trace in enumerate(traces):
        if not isinstance(trace, Mapping):
            raise FidelityError(f"trace at index {index} must be an object")
        trace_id = trace.get("trace_id")
        if not isinstance(trace_id, str) or not trace_id.strip():
            raise FidelityError(f"trace at index {index} requires a non-empty string 'trace_id'")
        if trace_id in seen_ids:
            raise FidelityError(f"duplicate trace_id '{trace_id}'")
        seen_ids.add(trace_id)
        for stage in ("source", "tool_args", "tool_result"):
            if not isinstance(trace.get(stage), Mapping):
                raise FidelityError(f"trace '{trace_id}' requires object field '{stage}'")


def _contract_from_json_schema(schema: Mapping[str, Any]) -> dict[str, Any]:
    """Convert an object JSON Schema plus optional x-* mappings to a field contract."""

    root_properties = schema.get("properties")
    if not isinstance(root_properties, Mapping) or not root_properties:
        raise FidelityError("JSON Schema contract requires a non-empty object field 'properties'")
    fields: dict[str, dict[str, Any]] = {}

    def visit(
        properties: Mapping[str, Any], required_names: set[str], prefix: str = "", parent_required: bool = True
    ) -> None:
        for property_name in sorted(properties):
            property_schema = properties[property_name]
            if not isinstance(property_name, str) or not property_name:
                raise FidelityError("JSON Schema property names must be non-empty strings")
            if not isinstance(property_schema, Mapping):
                raise FidelityError(f"JSON Schema property '{property_name}' must be an object")
            path = f"{prefix}.{property_name}" if prefix else property_name
            nested = property_schema.get("properties")
            if isinstance(nested, Mapping) and nested and "x-tool-path" not in property_schema:
                child_required = property_schema.get("required", [])
                if not isinstance(child_required, list) or not all(isinstance(item, str) for item in child_required):
                    raise FidelityError(f"JSON Schema property '{path}' required must be a list of strings")
                visit(nested, set(child_required), path, parent_required and property_name in required_names)
                continue
            schema_type = property_schema.get("type", "any")
            type_values = schema_type if isinstance(schema_type, list) else [schema_type]
            if not all(isinstance(item, str) for item in type_values):
                raise FidelityError(f"JSON Schema property '{path}' type must be a string or list of strings")
            non_null_types = [item for item in type_values if item != "null"]
            coercion = non_null_types[0] if len(non_null_types) == 1 else "any"
            if coercion not in COERCIONS:
                coercion = "any"
            spec: dict[str, Any] = {
                "source_path": property_schema.get("x-source-path", path),
                "tool_path": property_schema.get("x-tool-path", path),
                "result_path": property_schema.get("x-result-path", path),
                "required": parent_required and property_name in required_names,
                "nullable": "null" in type_values,
                "coercion": coercion,
            }
            for extension, contract_key in JSON_SCHEMA_EXTENSIONS.items():
                if extension in property_schema:
                    spec[contract_key] = property_schema[extension]
            fields[path] = spec

    required = schema.get("required", [])
    if not isinstance(required, list) or not all(isinstance(item, str) for item in required):
        raise FidelityError("JSON Schema root required must be a list of strings")
    visit(root_properties, set(required))
    return {"version": 1, "fields": fields}


def validate_contract(contract: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and normalize a representation contract."""

    if not isinstance(contract, Mapping):
        raise FidelityError("contract must be an object")
    if "fields" not in contract and ("$schema" in contract or "properties" in contract):
        contract = _contract_from_json_schema(contract)
    fields = contract.get("fields")
    if not isinstance(fields, Mapping) or not fields:
        raise FidelityError("contract requires a non-empty object field 'fields'")
    normalized_fields: dict[str, dict[str, Any]] = {}
    for name in sorted(fields):
        spec = fields[name]
        if not isinstance(name, str) or not name:
            raise FidelityError("contract field names must be non-empty strings")
        if not isinstance(spec, Mapping):
            raise FidelityError(f"contract field '{name}' must be an object")
        unknown = sorted(set(spec) - ALLOWED_FIELD_KEYS)
        if unknown:
            raise FidelityError(f"contract field '{name}' has unknown key(s): {', '.join(unknown)}")
        for required_path in ("source_path", "tool_path"):
            if not isinstance(spec.get(required_path), str) or not spec[required_path]:
                raise FidelityError(f"contract field '{name}' requires non-empty '{required_path}'")
        for path_key in PATH_KEYS:
            if path_key in spec and (not isinstance(spec[path_key], str) or not spec[path_key]):
                raise FidelityError(f"contract field '{name}' has invalid '{path_key}'")
        for boolean_key in ("required", "nullable"):
            if boolean_key in spec and not isinstance(spec[boolean_key], bool):
                raise FidelityError(f"contract field '{name}' requires boolean '{boolean_key}'")
        precision = spec.get("precision")
        if precision is not None and (isinstance(precision, bool) or not isinstance(precision, int) or precision < 1):
            raise FidelityError(f"contract field '{name}' precision must be a positive integer")
        dimensions = spec.get("dimensions")
        if dimensions is not None and (
            not isinstance(dimensions, list) or not all(isinstance(item, str) and item for item in dimensions)
        ):
            raise FidelityError(f"contract field '{name}' dimensions must be a list of strings")
        coercion = spec.get("coercion", "any")
        if coercion not in COERCIONS:
            raise FidelityError(
                f"contract field '{name}' coercion must be one of: {', '.join(sorted(COERCIONS))}"
            )
        if "unit" in spec and (not isinstance(spec["unit"], str) or not spec["unit"]):
            raise FidelityError(f"contract field '{name}' unit must be a non-empty string")
        if "missing_values" in spec and not isinstance(spec["missing_values"], list):
            raise FidelityError(f"contract field '{name}' missing_values must be a list")
        normalized = dict(spec)
        normalized.setdefault("required", True)
        normalized.setdefault("nullable", False)
        normalized.setdefault("coercion", "any")
        normalized_fields[name] = normalized
    return {"version": contract.get("version", 1), "fields": normalized_fields}


def get_path(data: Mapping[str, Any], path: str) -> Any:
    """Return a dot-separated dictionary path or the MISSING sentinel."""

    current: Any = data
    for segment in path.split("."):
        if not isinstance(current, Mapping) or segment not in current:
            return MISSING
        current = current[segment]
    return current


def _flatten_paths(value: Any, prefix: str = "") -> Iterable[tuple[str, Any]]:
    """Yield leaf paths for simple schema inference."""

    if isinstance(value, Mapping) and value:
        for key in sorted(value):
            next_prefix = f"{prefix}.{key}" if prefix else str(key)
            yield from _flatten_paths(value[key], next_prefix)
    elif prefix:
        yield prefix, value


def _coercion_for(value: Any) -> str:
    """Infer a conservative coercion label from a JSON value."""

    if value is None:
        return "any"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, Mapping):
        return "object"
    return "any"


def infer_contract(traces: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Infer same-path field mappings from source leaf values."""

    fields: dict[str, dict[str, Any]] = {}
    for path, value in _flatten_paths(traces[0]["source"]):
        fields[path] = {
            "source_path": path,
            "tool_path": path,
            "result_path": path,
            "required": True,
            "nullable": value is None,
            "coercion": _coercion_for(value),
        }
    if not fields:
        raise FidelityError("cannot infer a contract from an empty source object")
    return {"version": 1, "fields": fields}


def _safe_value(value: Any) -> Any:
    """Convert non-finite floats to deterministic JSON-safe strings."""

    if value is MISSING:
        return "<missing>"
    if isinstance(value, float) and not math.isfinite(value):
        if math.isnan(value):
            return "NaN"
        return "Infinity" if value > 0 else "-Infinity"
    if isinstance(value, list):
        return [_safe_value(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _safe_value(item) for key, item in value.items()}
    return value


def _display(value: Any) -> str:
    """Render a compact deterministic value for finding messages."""

    return json.dumps(_safe_value(value), sort_keys=True, separators=(",", ":"))


def _shape(value: Any) -> tuple[int, ...] | None:
    """Return a rectangular list shape, or None for ragged arrays."""

    if not isinstance(value, list):
        return ()
    if not value:
        return (0,)
    child_shapes = [_shape(item) for item in value]
    if any(shape is None for shape in child_shapes) or len(set(child_shapes)) != 1:
        return None
    child = child_shapes[0]
    return (len(value),) + (child or ())


def _leaf_count(value: Any) -> int:
    """Count scalar leaves in a nested list."""

    if not isinstance(value, list):
        return 1
    return sum(_leaf_count(item) for item in value)


def _is_number(value: Any) -> bool:
    """Return true for JSON numeric values while excluding booleans."""

    return isinstance(value, (int, float, Decimal)) and not isinstance(value, bool)


def _numeric_string(value: Any) -> Decimal | None:
    """Parse a finite numeric string as Decimal, otherwise return None."""

    if not isinstance(value, str) or not value.strip():
        return None
    try:
        number = Decimal(value)
    except InvalidOperation:
        return None
    return number if number.is_finite() else None


def _decimal(value: Any) -> Decimal | None:
    """Convert a finite number to Decimal without binary floating-point noise."""

    if not _is_number(value) or (isinstance(value, float) and not math.isfinite(value)):
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return None


def _significant_digits(value: Any) -> int | None:
    """Count significant decimal digits for a finite number."""

    decimal_value = _decimal(value)
    if decimal_value is None:
        parsed = _numeric_string(value)
        decimal_value = parsed
    if decimal_value is None:
        return None
    digits = decimal_value.normalize().as_tuple().digits
    return max(1, len(digits))


def _missing_kind(value: Any, spec: Mapping[str, Any]) -> str | None:
    """Classify null, NaN, and configured sentinel encodings."""

    if value is None:
        return "null"
    if isinstance(value, float) and math.isnan(value):
        return "NaN"
    for sentinel in spec.get("missing_values", []):
        if sentinel is None:
            continue
        if sentinel == "NaN" and isinstance(value, float) and math.isnan(value):
            return "NaN"
        if type(value) is type(sentinel) and value == sentinel:
            return "sentinel"
    return None


def _finding(
    trace_id: str,
    field: str,
    transition: str,
    code: str,
    severity: str,
    confidence: float,
    message: str,
) -> dict[str, Any]:
    """Construct one finding using the stable public output shape."""

    return {
        "trace_id": trace_id,
        "field": field,
        "transition": transition,
        "code": code,
        "severity": severity,
        "confidence": confidence,
        "message": message,
    }


def _compare_values(
    trace_id: str,
    field: str,
    transition: str,
    source: Any,
    observed: Any,
    spec: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Detect representation changes between two aligned values."""

    findings: list[dict[str, Any]] = []
    source_missing = _missing_kind(source, spec)
    observed_missing = _missing_kind(observed, spec)
    if source_missing:
        if not observed_missing:
            if observed == 0 and not isinstance(observed, bool):
                code, message = "zero_substitution", "Missing value was replaced with numeric zero."
            elif observed == "":
                code, message = "empty_string_substitution", "Missing value was replaced with an empty string."
            else:
                code, message = "missing_value_lost", f"Missing value was replaced with {_display(observed)}."
            findings.append(_finding(trace_id, field, transition, code, "error", 1.0, message))
        elif source_missing != observed_missing:
            findings.append(
                _finding(
                    trace_id,
                    field,
                    transition,
                    "missing_value_encoding_changed",
                    "warning",
                    1.0,
                    f"Missing-value encoding changed from {source_missing} to {observed_missing}.",
                )
            )
        return findings
    if observed_missing:
        findings.append(
            _finding(
                trace_id,
                field,
                transition,
                "non_missing_to_missing",
                "error",
                1.0,
                f"Non-missing value {_display(source)} became {observed_missing}.",
            )
        )
        return findings

    if isinstance(source, int) and not isinstance(source, bool) and abs(source) > SAFE_INTEGER_MAX:
        findings.append(
            _finding(
                trace_id,
                field,
                transition,
                "overflow_risk",
                "warning",
                0.95,
                f"Integer {_display(source)} exceeds the IEEE-754 safe integer range.",
            )
        )

    comparable_observed = observed
    if _is_number(source) and _numeric_string(observed) is not None:
        comparable_observed = Decimal(observed)
        findings.append(
            _finding(
                trace_id,
                field,
                transition,
                "numeric_type_coercion",
                "warning",
                1.0,
                f"Numeric value changed type from {type(source).__name__} to string.",
            )
        )
    elif type(source) is not type(observed):
        if _is_number(source) and _is_number(observed):
            findings.append(
                _finding(
                    trace_id,
                    field,
                    transition,
                    "numeric_type_coercion",
                    "warning",
                    1.0,
                    f"Numeric value changed type from {type(source).__name__} to {type(observed).__name__}.",
                )
            )
        else:
            findings.append(
                _finding(
                    trace_id,
                    field,
                    transition,
                    "type_coercion",
                    "error",
                    1.0,
                    f"Value changed type from {type(source).__name__} to {type(observed).__name__}.",
                )
            )
            return findings

    if isinstance(source, list) and isinstance(observed, list):
        source_shape, observed_shape = _shape(source), _shape(observed)
        if source_shape != observed_shape:
            if (
                source_shape
                and observed_shape
                and len(source_shape) > len(observed_shape)
                and len(observed_shape) == 1
                and _leaf_count(source) == _leaf_count(observed)
            ):
                code = "flattened_array"
                message = f"Array shape changed from {list(source_shape)} to {list(observed_shape)} by flattening."
            elif source_shape and observed_shape and sorted(source_shape) == sorted(observed_shape):
                code = "reordered_dimensions"
                message = f"Array dimensions changed order from {list(source_shape)} to {list(observed_shape)}."
            else:
                code = "array_shape_changed"
                message = f"Array shape changed from {_display(source_shape)} to {_display(observed_shape)}."
            findings.append(_finding(trace_id, field, transition, code, "error", 1.0, message))
        elif source != observed:
            findings.append(
                _finding(
                    trace_id,
                    field,
                    transition,
                    "array_values_changed",
                    "warning",
                    0.9,
                    "Array values changed while the array shape was preserved.",
                )
            )
        return findings

    if _is_number(source) and _is_number(comparable_observed):
        source_decimal, observed_decimal = _decimal(source), _decimal(comparable_observed)
        if source_decimal is not None and observed_decimal is not None and source_decimal != observed_decimal:
            observed_places = max(0, -observed_decimal.as_tuple().exponent)
            quantum = Decimal(1).scaleb(-observed_places)
            truncated = source_decimal.quantize(quantum, rounding=ROUND_DOWN)
            code = "numeric_truncation" if truncated == observed_decimal else "numeric_rounding"
            findings.append(
                _finding(
                    trace_id,
                    field,
                    transition,
                    code,
                    "warning",
                    0.99,
                    f"Numeric value changed from {_display(source)} to {_display(observed)}.",
                )
            )
            source_digits = _significant_digits(source)
            observed_digits = _significant_digits(observed)
            if source_digits is not None and observed_digits is not None and observed_digits < source_digits:
                findings.append(
                    _finding(
                        trace_id,
                        field,
                        transition,
                        "significant_digit_loss",
                        "warning",
                        0.99,
                        f"Significant digits decreased from {source_digits} to {observed_digits}.",
                    )
                )
        minimum_digits = spec.get("precision")
        observed_digits = _significant_digits(observed)
        if minimum_digits and observed_digits is not None and observed_digits < minimum_digits:
            findings.append(
                _finding(
                    trace_id,
                    field,
                    transition,
                    "precision_contract_violated",
                    "error",
                    0.99,
                    f"Observed value has {observed_digits} significant digits; contract requires at least {minimum_digits}.",
                )
            )
        return findings

    if source != observed:
        findings.append(
            _finding(
                trace_id,
                field,
                transition,
                "value_changed",
                "warning",
                0.9,
                f"Value changed from {_display(source)} to {_display(observed)}.",
            )
        )
    return findings


def _compare_metadata(
    trace_id: str,
    field: str,
    transition: str,
    base_stage: Mapping[str, Any],
    observed_stage: Mapping[str, Any],
    spec: Mapping[str, Any],
    base_prefix: str,
    observed_prefix: str,
) -> list[dict[str, Any]]:
    """Compare unit, axis, and dimension metadata for one transition."""

    findings: list[dict[str, Any]] = []
    base_unit_path = spec.get(f"{base_prefix}_unit_path")
    observed_unit_path = spec.get(f"{observed_prefix}_unit_path")
    base_unit = get_path(base_stage, base_unit_path) if base_unit_path else MISSING
    observed_unit = get_path(observed_stage, observed_unit_path) if observed_unit_path else MISSING
    expected_unit = spec.get("unit")
    if observed_unit_path and observed_unit is MISSING and (base_unit is not MISSING or expected_unit):
        findings.append(
            _finding(trace_id, field, transition, "dropped_unit", "error", 1.0, f"Expected unit '{expected_unit or base_unit}' is missing.")
        )
    elif observed_unit is not MISSING and expected_unit and observed_unit != expected_unit:
        findings.append(
            _finding(
                trace_id,
                field,
                transition,
                "unit_changed",
                "error",
                1.0,
                f"Unit {_display(observed_unit)} does not match contract unit {_display(expected_unit)}.",
            )
        )
    elif base_unit is not MISSING and observed_unit is not MISSING and base_unit != observed_unit:
        findings.append(
            _finding(
                trace_id,
                field,
                transition,
                "unit_changed",
                "error",
                1.0,
                f"Unit changed from {_display(base_unit)} to {_display(observed_unit)}.",
            )
        )

    base_axes_path = spec.get(f"{base_prefix}_axes_path")
    observed_axes_path = spec.get(f"{observed_prefix}_axes_path")
    base_axes = get_path(base_stage, base_axes_path) if base_axes_path else MISSING
    observed_axes = get_path(observed_stage, observed_axes_path) if observed_axes_path else MISSING
    if base_axes is not MISSING and observed_axes is MISSING:
        findings.append(_finding(trace_id, field, transition, "dropped_axes", "error", 1.0, "Axis metadata is missing."))
    elif isinstance(base_axes, list) and isinstance(observed_axes, list) and base_axes != observed_axes:
        same_members = sorted(_display(item) for item in base_axes) == sorted(_display(item) for item in observed_axes)
        if len(base_axes) == len(observed_axes) and same_members:
            code, message = "reordered_dimensions", f"Axis order changed from {_display(base_axes)} to {_display(observed_axes)}."
        elif len(base_axes) == len(observed_axes):
            code, message = "renamed_axes", f"Axis names changed from {_display(base_axes)} to {_display(observed_axes)}."
        else:
            code, message = "axes_changed", f"Axes changed from {_display(base_axes)} to {_display(observed_axes)}."
        findings.append(_finding(trace_id, field, transition, code, "error", 1.0, message))

    base_dimensions_path = spec.get(f"{base_prefix}_dimensions_path")
    observed_dimensions_path = spec.get(f"{observed_prefix}_dimensions_path")
    base_dimensions = get_path(base_stage, base_dimensions_path) if base_dimensions_path else MISSING
    observed_dimensions = get_path(observed_stage, observed_dimensions_path) if observed_dimensions_path else MISSING
    if base_dimensions is not MISSING and observed_dimensions is MISSING:
        findings.append(
            _finding(trace_id, field, transition, "dropped_dimensions", "error", 1.0, "Dimension metadata is missing.")
        )
    elif base_dimensions is not MISSING and observed_dimensions is not MISSING and base_dimensions != observed_dimensions:
        findings.append(
            _finding(
                trace_id,
                field,
                transition,
                "dimension_metadata_changed",
                "error",
                1.0,
                f"Dimension metadata changed from {_display(base_dimensions)} to {_display(observed_dimensions)}.",
            )
        )
    return findings


def _coercion_rules(spec: Mapping[str, Any]) -> list[str]:
    """Generate deterministic adapter rules from one field contract."""

    rules = [f"preserve-{spec.get('coercion', 'any')}-type"]
    if spec.get("unit"):
        rules.append(f"preserve-unit:{spec['unit']}")
    if spec.get("dimensions"):
        rules.append(f"preserve-dimension-order:{','.join(spec['dimensions'])}")
    if spec.get("precision"):
        rules.append(f"minimum-significant-digits:{spec['precision']}")
    if spec.get("nullable"):
        rules.append("preserve-missing-value-semantics")
    else:
        rules.append("reject-null")
    return rules


def _adapter_recommendation(contract: Mapping[str, Any]) -> dict[str, Any]:
    """Build the machine-readable adapter recommendation."""

    fields = []
    for name, spec in contract["fields"].items():
        fields.append(
            {
                "field": name,
                "source_path": spec["source_path"],
                "tool_path": spec["tool_path"],
                "result_path": spec.get("result_path"),
                "required": spec["required"],
                "unit": spec.get("unit"),
                "dimensions": spec.get("dimensions"),
                "nullable": spec["nullable"],
                "precision": spec.get("precision"),
                "coercion": spec["coercion"],
                "coercion_rules": _coercion_rules(spec),
            }
        )
    return {"schema_version": SCHEMA_VERSION, "fields": fields}


def audit_traces(
    traces: Sequence[Mapping[str, Any]], contract: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Audit traces and return a deterministic fidelity report and adapter recommendation."""

    validate_traces(traces)
    normalized_contract = validate_contract(contract if contract is not None else infer_contract(traces))
    findings: list[dict[str, Any]] = []
    for trace in traces:
        trace_id = trace["trace_id"]
        for field, spec in normalized_contract["fields"].items():
            source = get_path(trace["source"], spec["source_path"])
            tool_value = get_path(trace["tool_args"], spec["tool_path"])
            if source is MISSING:
                if spec["required"]:
                    findings.append(
                        _finding(
                            trace_id,
                            field,
                            "source->tool_args",
                            "source_field_missing",
                            "error",
                            1.0,
                            f"Required source path '{spec['source_path']}' is missing.",
                        )
                    )
                continue
            if tool_value is MISSING:
                severity = "error" if spec["required"] else "warning"
                findings.append(
                    _finding(
                        trace_id,
                        field,
                        "source->tool_args",
                        "omitted_field",
                        severity,
                        1.0,
                        f"Tool arguments omit mapped path '{spec['tool_path']}'.",
                    )
                )
            else:
                findings.extend(_compare_values(trace_id, field, "source->tool_args", source, tool_value, spec))
            findings.extend(
                _compare_metadata(
                    trace_id,
                    field,
                    "source->tool_args",
                    trace["source"],
                    trace["tool_args"],
                    spec,
                    "source",
                    "tool",
                )
            )

            result_path = spec.get("result_path")
            if result_path:
                result_value = get_path(trace["tool_result"], result_path)
                if result_value is MISSING:
                    severity = "error" if spec["required"] else "warning"
                    findings.append(
                        _finding(
                            trace_id,
                            field,
                            "tool_args->tool_result",
                            "omitted_result_field",
                            severity,
                            1.0,
                            f"Tool result omits mapped path '{result_path}'.",
                        )
                    )
                elif tool_value is not MISSING:
                    findings.extend(
                        _compare_values(trace_id, field, "tool_args->tool_result", tool_value, result_value, spec)
                    )
                findings.extend(
                    _compare_metadata(
                        trace_id,
                        field,
                        "tool_args->tool_result",
                        trace["tool_args"],
                        trace["tool_result"],
                        spec,
                        "tool",
                        "result",
                    )
                )

    counts = {severity: sum(item["severity"] == severity for item in findings) for severity in ("error", "warning", "info")}
    status = "fail" if counts["error"] else "warn" if counts["warning"] else "pass"
    return {
        "fidelity_report": {
            "schema_version": SCHEMA_VERSION,
            "status": status,
            "trace_count": len(traces),
            "finding_count": len(findings),
            "severity_counts": counts,
            "findings": findings,
        },
        "adapter_recommendation": _adapter_recommendation(normalized_contract),
    }


def format_report(report: Mapping[str, Any], output_format: str = "json") -> str:
    """Serialize a report as stable JSON or concise human-readable text."""

    if output_format == "json":
        return json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    fidelity = report["fidelity_report"]
    counts = fidelity["severity_counts"]
    lines = [
        "FidelityLoom fidelity report",
        f"Status: {fidelity['status'].upper()}",
        f"Traces: {fidelity['trace_count']}",
        f"Findings: {fidelity['finding_count']} (error={counts['error']}, warning={counts['warning']}, info={counts['info']})",
        "",
        "Findings:",
    ]
    if fidelity["findings"]:
        for item in fidelity["findings"]:
            lines.append(
                f"- [{item['severity'].upper()}] {item['trace_id']} {item['transition']} "
                f"{item['field']} {item['code']}: {item['message']}"
            )
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "Adapter recommendation:",
            json.dumps(report["adapter_recommendation"], indent=2, ensure_ascii=False, allow_nan=False),
        ]
    )
    return "\n".join(lines) + "\n"


def _threshold_failed(report: Mapping[str, Any], fail_on: str) -> bool:
    """Return whether findings meet the requested CI failure threshold."""

    threshold = SEVERITY_RANK[fail_on]
    return threshold > 0 and any(
        SEVERITY_RANK[item["severity"]] >= threshold for item in report["fidelity_report"]["findings"]
    )


def _write_or_print(content: str, output_path: str | None) -> None:
    """Write only when an explicit output path is supplied; otherwise print to stdout."""

    if output_path:
        try:
            Path(output_path).write_text(content, encoding="utf-8")
        except OSError as exc:
            raise FidelityError(f"cannot write output file '{output_path}': {exc}") from exc
    else:
        sys.stdout.write(content)


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""

    parser = argparse.ArgumentParser(
        description="Audit representation fidelity across source, tool arguments, and tool results."
    )
    parser.add_argument("input", nargs="?", help="JSONL trace file")
    parser.add_argument(
        "--contract",
        help="JSON contract file (default: FIDELITYLOOM_CONTRACT, then inferred same-path contract)",
    )
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default=os.getenv("FIDELITYLOOM_FORMAT", "json"),
        help="report format (default: %(default)s; env: FIDELITYLOOM_FORMAT)",
    )
    parser.add_argument("--output", help="explicit output file; overwrites that file if it exists")
    parser.add_argument(
        "--fail-on",
        choices=("none", "warning", "error"),
        default=os.getenv("FIDELITYLOOM_FAIL_ON", "none"),
        help="return exit code 1 at or above this severity (default: %(default)s)",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="run the built-in offline deterministic sample and internal assertions",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""

    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.format not in {"json", "text"}:
            raise FidelityError("FIDELITYLOOM_FORMAT must be 'json' or 'text'")
        if args.fail_on not in SEVERITY_RANK:
            raise FidelityError("FIDELITYLOOM_FAIL_ON must be 'none', 'warning', or 'error'")
        if args.selftest:
            if args.input or args.contract:
                raise FidelityError("--selftest cannot be combined with input or --contract")
            report = audit_traces(SAMPLE_TRACES, SAMPLE_CONTRACT)
            codes = {item["code"] for item in report["fidelity_report"]["findings"]}
            required_codes = {
                "dropped_unit",
                "flattened_array",
                "numeric_rounding",
                "numeric_type_coercion",
                "overflow_risk",
                "reordered_dimensions",
                "significant_digit_loss",
                "zero_substitution",
            }
            missing_codes = sorted(required_codes - codes)
            if missing_codes:
                raise FidelityError(f"selftest did not produce expected finding(s): {', '.join(missing_codes)}")
            _write_or_print(format_report(report, args.format), args.output)
            return 0
        if not args.input:
            parser.error("an input JSONL file is required unless --selftest is used")
        traces = load_jsonl(args.input)
        contract_path = args.contract or os.getenv("FIDELITYLOOM_CONTRACT")
        contract = load_contract(contract_path) if contract_path else None
        report = audit_traces(traces, contract)
        _write_or_print(format_report(report, args.format), args.output)
        return 1 if _threshold_failed(report, args.fail_on) else 0
    except FidelityError as exc:
        print(f"fidelityloom: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
