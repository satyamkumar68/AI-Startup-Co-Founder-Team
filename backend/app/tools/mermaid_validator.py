import re
from typing import Dict, Any


class MermaidValidatorTool:
    """Tool to validate and sanitize Mermaid diagram syntax."""

    VALID_DIAGRAM_TYPES = [
        "graph",
        "flowchart",
        "sequenceDiagram",
        "classDiagram",
        "stateDiagram",
        "erDiagram",
        "gantt",
        "pie"
    ]

    def sanitize(self, diagram_code: str) -> str:
        """Sanitize Mermaid diagram syntax to ensure clean rendering."""
        cleaned = diagram_code.strip()
        
        # 1. Remove markdown fences if present
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        lines = cleaned.splitlines()
        if not lines:
            return "flowchart TD\n    Client[Client App] --> API[API Gateway]"

        # 2. Check and normalize diagram type header
        first_non_empty = -1
        for idx, l in enumerate(lines):
            if l.strip():
                first_non_empty = idx
                break

        if first_non_empty == -1:
            return "flowchart TD\n    Client[Client App] --> API[API Gateway]"

        first_line = lines[first_non_empty].strip()
        has_valid_type = any(first_line.startswith(t) for t in self.VALID_DIAGRAM_TYPES)
        if not has_valid_type:
            if any(sym in first_line for sym in ["-->", "->", "→", "[", "(", "{"]):
                lines.insert(first_non_empty, "flowchart TD")

        sanitized_lines = []
        arrow_pattern = re.compile(r'(?<![-.=\w])(?:→|⇒|—>)(?![-.=>\w])')
        single_dash_arrow = re.compile(r'(?<![-.=\w])->(?![-.=>\w])')

        for line in lines:
            stripped = line.strip()
            # Skip comments, headers, subgraphs, end blocks
            if (
                not stripped
                or stripped.startswith("%%")
                or any(stripped.startswith(t) for t in self.VALID_DIAGRAM_TYPES)
                or stripped.startswith("subgraph")
                or stripped.startswith("end")
            ):
                sanitized_lines.append(line)
                continue

            l = line

            # Step A: Replace unicode arrows and single-dash arrows
            l = arrow_pattern.sub('-->', l)
            l = single_dash_arrow.sub('-->', l)

            # Step B: Fix spaces in node IDs before shape delimiters (e.g. "Patient Support[(Django)]" -> "Patient_Support[(Django)]")
            def fix_id_before_shape(match):
                prefix = match.group(1)
                node_id = match.group(2)
                shape_open = match.group(3)
                clean_id = re.sub(r'\s+', '_', node_id.strip())
                return f"{prefix}{clean_id}{shape_open}"

            l = re.sub(
                r'(^|\s*-->\s*|\s*==>\s*|\s*-\.->\s*|\|[^|\n]*\|\s*)([A-Za-z0-9_]+(?:\s+[A-Za-z0-9_]+)+)(\s*(?:\[\(|\(\[|\[\[|\(\(|\{\{|\[|\(|\{|\>))',
                fix_id_before_shape,
                l
            )

            # Step C: Fix bare multi-word node IDs between arrows or at line boundaries
            for _ in range(3):
                l = re.sub(
                    r'(^\s*)([A-Za-z0-9_]+(?:\s+[A-Za-z0-9_]+)+)(\s+(?:-->|==>|-\.->))',
                    lambda m: f"{m.group(1)}{re.sub(r'\s+', '_', m.group(2).strip())} {m.group(3).strip()}",
                    l
                )
                l = re.sub(
                    r'((?:-->|==>|-\.->)\s+)([A-Za-z0-9_]+(?:\s+[A-Za-z0-9_]+)+)(\s+(?:-->|==>|-\.->))',
                    lambda m: f"{m.group(1)}{re.sub(r'\s+', '_', m.group(2).strip())} {m.group(3).strip()}",
                    l
                )
                l = re.sub(
                    r'((?:-->|==>|-\.->)\s+)([A-Za-z0-9_]+(?:\s+[A-Za-z0-9_]+)+)(\s*(?:$|;))',
                    lambda m: f"{m.group(1)}{re.sub(r'\s+', '_', m.group(2).strip())}{m.group(3)}",
                    l
                )

            # Step D: Quote unquoted labels with parentheses or special characters inside simple brackets [ ... ]
            def quote_problematic_labels(match):
                node_id = match.group(1)
                inner = match.group(2)
                if not (inner.startswith('"') and inner.endswith('"')):
                    if any(ch in inner for ch in ['(', ')', ':', '&']):
                        escaped = inner.replace('"', "'")
                        return f'{node_id}["{escaped}"]'
                return match.group(0)

            l = re.sub(r'([A-Za-z0-9_]+)\[([^\(\[\"\n][^\]\n]*)\]', quote_problematic_labels, l)

            sanitized_lines.append(l)

        return "\n".join(sanitized_lines)

    def validate(self, diagram_code: str) -> Dict[str, Any]:
        """Validate and sanitize Mermaid diagram syntax."""
        sanitized = self.sanitize(diagram_code)
        
        lines = [line.strip() for line in sanitized.splitlines() if line.strip()]
        first_line = lines[0] if lines else ""
        has_valid_type = any(first_line.startswith(t) for t in self.VALID_DIAGRAM_TYPES)

        issues = []
        if not has_valid_type:
            issues.append(f"Diagram must begin with one of {self.VALID_DIAGRAM_TYPES}; found '{first_line}'.")

        # Check for unclosed brackets or delimiters
        open_brackets = sanitized.count("[")
        close_brackets = sanitized.count("]")
        if open_brackets != close_brackets:
            issues.append(f"Mismatched square brackets: {open_brackets} '[' vs {close_brackets} ']'.")

        open_parens = sanitized.count("(")
        close_parens = sanitized.count(")")
        if open_parens != close_parens:
            issues.append(f"Mismatched parentheses: {open_parens} '(' vs {close_parens} ')'.")

        return {
            "valid": len(issues) == 0,
            "sanitized_code": sanitized,
            "issues": issues
        }
