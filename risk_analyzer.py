#!/usr/bin/env python3
"""Risk Analyzer System.

A pure-Python command-line program for validating,
scoring, prioritising, and reporting operational risks.

It uses only Python's standard library and can be run on Windows, macOS, or Linux.
"""

import argparse
import csv
import json
import sys
import tempfile
import unittest
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_THRESHOLDS = {
    "Low": 1,
    "Medium": 5,
    "High": 10,
    "Critical": 17,
}

RISK_FIELDS = [
    "id",
    "title",
    "description",
    "category",
    "likelihood",
    "impact",
    "owner",
    "status",
    "mitigation",
]


class RiskValidationError(ValueError):
    """Raised when a risk record contains invalid data."""


# ---------------------------------------------------------------------------
# Data model and validation
# ---------------------------------------------------------------------------

@dataclass
class Risk:
    """A single operational risk and its supporting information."""

    id: str
    title: str
    description: str = ""
    category: str = "General"
    likelihood: int = 1
    impact: int = 1
    owner: str = "Unassigned"
    status: str = "Open"
    mitigation: str = ""

    def __post_init__(self) -> None:
        if not str(self.id).strip():
            raise RiskValidationError("id is required")
        if not str(self.title).strip():
            raise RiskValidationError("title is required")

        for name in ("likelihood", "impact"):
            try:
                value = int(getattr(self, name))
            except (TypeError, ValueError) as error:
                raise RiskValidationError(
                    f"{name} must be an integer from 1 to 5"
                ) from error
            if value < 1 or value > 5:
                raise RiskValidationError(f"{name} must be between 1 and 5")
            setattr(self, name, value)

    @property
    def score(self) -> int:
        """Calculate the risk score using likelihood multiplied by impact."""
        return self.likelihood * self.impact

    @classmethod
    def from_dictionary(cls, values: dict) -> "Risk":
        """Create a Risk while ignoring calculated or unknown input fields."""
        if not isinstance(values, dict):
            raise RiskValidationError("each risk must be a JSON object or CSV row")
        clean_values = {key: values[key] for key in RISK_FIELDS if key in values}
        return cls(**clean_values)

    def to_dictionary(self) -> dict:
        """Return a JSON/CSV-friendly representation of this risk."""
        result = asdict(self)
        result["score"] = self.score
        return result


# ---------------------------------------------------------------------------
# Configuration and analysis logic
# ---------------------------------------------------------------------------

def load_thresholds(config_path: Optional[str] = None) -> Dict[str, int]:
    """Load priority thresholds from JSON, or use safe defaults."""
    if config_path is None:
        return DEFAULT_THRESHOLDS.copy()

    try:
        config = json.loads(Path(config_path).read_text(encoding="utf-8"))
        thresholds = config.get("thresholds", config)
        if set(thresholds) != set(DEFAULT_THRESHOLDS):
            raise ValueError("thresholds must contain Low, Medium, High and Critical")
        values = {name: int(value) for name, value in thresholds.items()}
        if any(value < 1 for value in values.values()):
            raise ValueError("thresholds must be positive")
        if list(values.values()) != sorted(values.values()):
            raise ValueError("threshold values must be in ascending order")
        return values
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        raise ValueError(f"could not read configuration: {error}") from error


def classify_score(score: int, thresholds: Dict[str, int]) -> str:
    """Map a score to the highest matching priority band."""
    priority = "Low"
    for name, minimum in sorted(thresholds.items(), key=lambda item: item[1]):
        if score >= minimum:
            priority = name
    return priority


def analyze_risks(risks: List[Risk], thresholds: Dict[str, int]) -> List[dict]:
    """Score and sort risks from highest score to lowest score."""
    results = []
    for risk in risks:
        result = risk.to_dictionary()
        result["priority"] = classify_score(risk.score, thresholds)
        results.append(result)

    # Sort by score descending, then ID ascending for predictable output.
    return sorted(results, key=lambda item: (-item["score"], item["id"]))


def build_summary(results: List[dict]) -> Dict[str, int]:
    """Count how many analyzed risks belong to each priority."""
    return {
        priority: sum(item["priority"] == priority for item in results)
        for priority in ("Critical", "High", "Medium", "Low")
    }


# ---------------------------------------------------------------------------
# File input and output
# ---------------------------------------------------------------------------

def load_risks(input_path: str) -> List[Risk]:
    """Load validated risks from a JSON list or a CSV file."""
    path = Path(input_path)
    try:
        if path.suffix.lower() == ".json":
            raw_data = json.loads(path.read_text(encoding="utf-8"))
        elif path.suffix.lower() == ".csv":
            with path.open("r", newline="", encoding="utf-8") as file:
                raw_data = list(csv.DictReader(file))
        else:
            raise ValueError("input file must have a .json or .csv extension")

        if not isinstance(raw_data, list):
            raise ValueError("JSON input must contain a list of risks")
        return [Risk.from_dictionary(item) for item in raw_data]
    except (OSError, json.JSONDecodeError, RiskValidationError, ValueError) as error:
        raise ValueError(f"could not load '{input_path}': {error}") from error


def write_report(results: List[dict], output_path: str, report_format: str) -> None:
    """Write analyzed results as text, JSON, or CSV."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if report_format == "json":
        path.write_text(json.dumps(results, indent=2), encoding="utf-8")
        return

    if report_format == "csv":
        fields = RISK_FIELDS + ["score", "priority"]
        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()
            writer.writerows(results)
        return

    if report_format == "text":
        lines = ["Risk Analyzer Report", "=" * 20]
        for item in results:
            lines.append(
                f"{item['id']} | {item['title']} | "
                f"score={item['score']} | priority={item['priority']}"
            )
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return

    raise ValueError("report format must be text, json, or csv")


# ---------------------------------------------------------------------------
# Command-line interface
# ---------------------------------------------------------------------------

def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate, score, prioritise, and report operational risks."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command_name in ("analyze", "report"):
        command = subparsers.add_parser(command_name)
        command.add_argument("--input", required=True, help="JSON or CSV risk file")
        command.add_argument("--config", help="optional JSON threshold configuration")
        if command_name == "report":
            command.add_argument("--output", required=True)
            command.add_argument(
                "--format", choices=("text", "json", "csv"), default="text"
            )

    add_command = subparsers.add_parser("add", help="enter one risk interactively")
    add_command.add_argument("--output", default="risk.json")
    return parser


def add_risk_interactively(output_path: str) -> None:
    """Prompt for one risk and save it as a JSON list."""
    values = {}
    for field in RISK_FIELDS:
        values[field] = input(f"{field}: ").strip()
    risk = Risk.from_dictionary(values)
    Path(output_path).write_text(
        json.dumps([risk.to_dictionary()], indent=2), encoding="utf-8"
    )
    print(f"Saved risk to {output_path}")


def run_application(arguments: Optional[List[str]] = None) -> int:
    """Run the CLI and return a process exit code."""
    args = make_parser().parse_args(arguments)
    try:
        if args.command == "add":
            add_risk_interactively(args.output)
            return 0

        risks = load_risks(args.input)
        results = analyze_risks(risks, load_thresholds(args.config))

        if args.command == "report":
            write_report(results, args.output, args.format)
            print(f"Saved report to {args.output}")
        else:
            print("Risk Analyzer System")
            print("--------------------")
            print(f"Risks analyzed: {len(results)}")
            print(" | ".join(f"{key}: {value}" for key, value in build_summary(results).items()))
            print("\nID | TITLE | SCORE | PRIORITY")
            for item in results:
                print(f"{item['id']} | {item['title']} | {item['score']} | {item['priority']}")
        return 0
    except (OSError, ValueError, RiskValidationError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


# ---------------------------------------------------------------------------
# Built-in tests: no additional test files or third-party packages required.
# Run with: python risk_analyzer.py --self-test
# ---------------------------------------------------------------------------

class RiskAnalyzerTests(unittest.TestCase):
    """Unit tests for the main model, algorithm, validation, and I/O."""

    def test_score_calculation(self):
        self.assertEqual(Risk("R1", "Outage", likelihood=4, impact=5).score, 20)

    def test_invalid_rating_is_rejected(self):
        with self.assertRaises(RiskValidationError):
            Risk("R1", "Outage", likelihood=6, impact=1)

    def test_priority_classification(self):
        self.assertEqual(classify_score(20, DEFAULT_THRESHOLDS), "Critical")

    def test_results_are_sorted(self):
        risks = [
            Risk("LOW", "Small issue", likelihood=1, impact=1),
            Risk("HIGH", "Large issue", likelihood=5, impact=5),
        ]
        results = analyze_risks(risks, DEFAULT_THRESHOLDS)
        self.assertEqual(results[0]["id"], "HIGH")

    def test_json_load_and_report(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "risks.json"
            target = Path(directory) / "report.json"
            source.write_text(
                json.dumps([{"id": "R1", "title": "Test", "likelihood": 2, "impact": 3}]),
                encoding="utf-8",
            )
            results = analyze_risks(load_risks(str(source)), DEFAULT_THRESHOLDS)
            write_report(results, str(target), "json")
            saved = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(saved[0]["score"], 6)


def run_tests() -> int:
    """Run the built-in unit tests."""
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(RiskAnalyzerTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.argv.remove("--self-test")
        raise SystemExit(run_tests())
    raise SystemExit(run_application())
