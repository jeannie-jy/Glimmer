"""Parse pytest JSON reports into structured failure lists."""
from harness.models import Failure


def parse_pytest_structured(structured: dict) -> list[Failure]:
    """Extract failures from a pytest JSON report's structured field."""
    failures = []
    for f in structured.get("failures", []):
        failures.append(Failure(
            file=f.get("file", ""),
            line=f.get("line"),
            function=f.get("function", ""),
            message=f.get("message", ""),
        ))
    return failures
