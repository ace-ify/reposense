import ast
import operator
import re
from typing import Any, Literal
from backend.app.schemas.question import CalculationRecord

# Allowed AST math operators for safe formula execution
OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
    ast.Pow: operator.pow,
}

class SafeEvaluator(ast.NodeVisitor):
    def __init__(self, variables: dict[str, float]):
        self.variables = variables

    def visit(self, node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return self.visit(node.body)
        elif isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return float(node.value)
            raise ValueError(f"Unsupported constant type: {type(node.value)}")
        elif isinstance(node, ast.Name):
            if node.id in self.variables:
                return float(self.variables[node.id])
            raise ValueError(f"Undefined variable in formula: {node.id}")
        elif isinstance(node, ast.BinOp):
            left = self.visit(node.left)
            right = self.visit(node.right)
            op_type = type(node.op)
            if op_type in OPERATORS:
                if op_type is ast.Div and right == 0:
                    raise ZeroDivisionError("Division by zero in formula calculation")
                return OPERATORS[op_type](left, right)
            raise ValueError(f"Unsupported operator: {op_type}")
        elif isinstance(node, ast.UnaryOp):
            operand = self.visit(node.operand)
            op_type = type(node.op)
            if op_type in OPERATORS:
                return OPERATORS[op_type](operand)
            raise ValueError(f"Unsupported unary operator: {op_type}")
        else:
            raise ValueError(f"Unsupported AST node in formula: {type(node).__name__}")


class DeterministicCalculator:
    """
    Deterministic arithmetic calculator ensuring 100% mathematical precision
    and generating auditable calculation records without LLM arithmetic hallucinations.
    """

    SCALE_MAP = {
        "t": 1e12,
        "trillion": 1e12,
        "b": 1e9,
        "billion": 1e9,
        "bn": 1e9,
        "m": 1e6,
        "million": 1e6,
        "mn": 1e6,
        "k": 1e3,
        "thousand": 1e3,
    }

    @classmethod
    def parse_number(cls, raw: Any) -> float | None:
        """Parse raw number string with currency, commas, parentheses, or scale suffixes."""
        if raw is None:
            return None
        if isinstance(raw, (int, float)):
            return float(raw)

        s = str(raw).strip()
        if not s:
            return None

        # Check for parentheses indicating negative: (123.4) -> -123.4
        is_negative = False
        if s.startswith("(") and s.endswith(")"):
            is_negative = True
            s = s[1:-1].strip()
        elif s.startswith("-"):
            is_negative = True
            s = s[1:].strip()

        # Remove currency symbols and formatting commas
        s = re.sub(r"[\$,€,£,¥]", "", s).replace(",", "").strip()

        # Handle percentage suffix
        if s.endswith("%"):
            s = s[:-1].strip()

        # Check for scale suffix
        multiplier = 1.0
        suffix_match = re.search(r"([a-zA-Z]+)$", s)
        if suffix_match:
            suffix = suffix_match.group(1).lower()
            if suffix in cls.SCALE_MAP:
                multiplier = cls.SCALE_MAP[suffix]
                s = s[: -len(suffix)].strip()

        try:
            val = float(s) * multiplier
            return -val if is_negative else val
        except ValueError:
            return None

    def percentage_change(
        self,
        old_val: float,
        new_val: float,
        old_label: str = "period_1",
        new_label: str = "period_2",
        unit: str = "%",
    ) -> CalculationRecord:
        if old_val == 0:
            raise ZeroDivisionError("Cannot compute percentage change from base value of 0")

        pct = ((new_val - old_val) / abs(old_val)) * 100.0
        rounded = round(pct, 2)
        formula = f"(({new_val} - {old_val}) / abs({old_val})) * 100"
        audit = (
            f"Percentage change from {old_label} ({old_val}) to {new_label} ({new_val}): "
            f"({new_val} - {old_val}) / {abs(old_val)} * 100 = {rounded}%"
        )

        return CalculationRecord(
            operation="percentage_change",
            formula=formula,
            raw_values={old_label: old_val, new_label: new_val},
            normalized_values={old_label: old_val, new_label: new_val},
            result=rounded,
            unit=unit,
            audit_trail=audit,
        )

    def difference(
        self,
        val_a: float,
        val_b: float,
        label_a: str = "val_a",
        label_b: str = "val_b",
        unit: str | None = None,
    ) -> CalculationRecord:
        diff = val_a - val_b
        rounded = round(diff, 2)
        formula = f"{val_a} - {val_b}"
        audit = f"Difference between {label_a} ({val_a}) and {label_b} ({val_b}): {val_a} - {val_b} = {rounded}"

        return CalculationRecord(
            operation="difference",
            formula=formula,
            raw_values={label_a: val_a, label_b: val_b},
            normalized_values={label_a: val_a, label_b: val_b},
            result=rounded,
            unit=unit,
            audit_trail=audit,
        )

    def ratio(
        self,
        numerator: float,
        denominator: float,
        num_label: str = "part",
        denom_label: str = "total",
        as_percentage: bool = True,
        unit: str = "%",
    ) -> CalculationRecord:
        if denominator == 0:
            raise ZeroDivisionError("Cannot compute ratio with denominator of 0")

        val = (numerator / denominator) * (100.0 if as_percentage else 1.0)
        rounded = round(val, 2)
        formula = f"({numerator} / {denominator}) * 100" if as_percentage else f"{numerator} / {denominator}"
        audit = f"Ratio of {num_label} ({numerator}) to {denom_label} ({denominator}): {formula} = {rounded}{unit if as_percentage else ''}"

        return CalculationRecord(
            operation="ratio",
            formula=formula,
            raw_values={num_label: numerator, denom_label: denominator},
            normalized_values={num_label: numerator, denom_label: denominator},
            result=rounded,
            unit=unit if as_percentage else None,
            audit_trail=audit,
        )

    def aggregate(
        self,
        values: list[float],
        operation: Literal["sum", "mean", "min", "max"],
        labels: list[str] | None = None,
        unit: str | None = None,
    ) -> CalculationRecord:
        if not values:
            raise ValueError("Cannot aggregate empty list of values")

        if operation == "sum":
            res = sum(values)
            formula = " + ".join(str(v) for v in values)
        elif operation == "mean":
            res = sum(values) / len(values)
            formula = f"({' + '.join(str(v) for v in values)}) / {len(values)}"
        elif operation == "min":
            res = min(values)
            formula = f"min({', '.join(str(v) for v in values)})"
        elif operation == "max":
            res = max(values)
            formula = f"max({', '.join(str(v) for v in values)})"
        else:
            raise ValueError(f"Unsupported aggregation operation: {operation}")

        rounded = round(res, 2)
        raw_vals = {labels[i] if labels and i < len(labels) else f"val_{i}": v for i, v in enumerate(values)}

        return CalculationRecord(
            operation=operation,
            formula=formula,
            raw_values=raw_vals,
            normalized_values=raw_vals,
            result=rounded,
            unit=unit,
            audit_trail=f"{operation.upper()}({list(raw_vals.values())}) = {rounded}",
        )

    def evaluate_safe_expression(
        self, formula_str: str, variables: dict[str, float], unit: str | None = None
    ) -> CalculationRecord:
        parsed_tree = ast.parse(formula_str, mode="eval")
        evaluator = SafeEvaluator(variables)
        result = evaluator.visit(parsed_tree)
        rounded = round(result, 2)

        return CalculationRecord(
            operation="custom_formula",
            formula=formula_str,
            raw_values=variables,
            normalized_values=variables,
            result=rounded,
            unit=unit,
            audit_trail=f"Evaluated '{formula_str}' with {variables} => {rounded}",
        )
