import ast
import re
from dataclasses import dataclass
from fractions import Fraction


ENGINE_VERSION = "1.0.0"
WORDS = re.compile(r"\b[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'-]{2,}\b")
COMMON = {"the", "and", "that", "this", "with", "from", "have", "into", "your", "pour", "avec", "dans", "une", "les", "des"}


@dataclass(frozen=True)
class SubjectPolicy:
    name: str
    dimensions: tuple[str, ...]
    instructions: str
    subjective: bool = False


POLICIES = {
    "maths": SubjectPolicy("maths", ("symbolic_equivalence", "method", "formula", "substitution", "units", "rounding"),
        "Check symbolic equivalence and the complete method separately. Award an official method point when valid working is shown even if the final answer is wrong. Check formula, substitution, units and requested rounding independently."),
    "biology": SubjectPolicy("science", ("terminology", "causal_reasoning", "experiment", "variables", "calculation", "conclusion"),
        "Check precise scientific terminology, linked cause and effect, experimental method, independent/dependent/control variables, calculation working and evidence-based conclusions."),
    "chemistry": SubjectPolicy("science", ("terminology", "causal_reasoning", "experiment", "variables", "calculation", "conclusion"),
        "Check precise scientific terminology, linked cause and effect, experimental method, variables, calculation working including units, and evidence-based conclusions."),
    "physics": SubjectPolicy("science", ("terminology", "causal_reasoning", "experiment", "variables", "calculation", "conclusion"),
        "Check precise scientific terminology, linked cause and effect, experimental method, variables, formula/substitution/units and evidence-based conclusions."),
    "human-biology": SubjectPolicy("science", ("terminology", "causal_reasoning", "experiment", "variables", "calculation", "conclusion"),
        "Check precise biological terminology, linked cause and effect, experimental method, variables, calculations and evidence-based conclusions."),
    "ict": SubjectPolicy("ict", ("vocabulary", "scenario_application", "trade_offs", "extended_reasoning"),
        "Check accurate ICT vocabulary, explicit application to the named scenario, balanced trade-offs and linked extended reasoning."),
    "english": SubjectPolicy("english", ("task_fulfilment", "evidence", "organisation", "language"),
        "Use only the approved task rubric. Check task fulfilment, relevant textual evidence, organisation and language. Treat interpretations as subjective and request review when evidence is ambiguous.", True),
    "french": SubjectPolicy("french", ("comprehension", "vocabulary", "grammar", "communication"),
        "Use only the approved comprehension or writing rubric. Check comprehension, appropriate vocabulary, grammatical accuracy and successful communication.", True),
}


def policy(subject_id: str) -> SubjectPolicy:
    return POLICIES.get(subject_id, SubjectPolicy(subject_id, ("rubric_alignment",), "Apply only the approved subject rubric."))


def _safe_value(node: ast.AST, values: dict[str, Fraction]) -> Fraction:
    if isinstance(node, ast.Expression): return _safe_value(node.body, values)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)): return Fraction(str(node.value))
    if isinstance(node, ast.Name) and node.id in values: return values[node.id]
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub): return -_safe_value(node.operand, values)
    if isinstance(node, ast.BinOp):
        left, right = _safe_value(node.left, values), _safe_value(node.right, values)
        if isinstance(node.op, ast.Add): return left + right
        if isinstance(node.op, ast.Sub): return left - right
        if isinstance(node.op, ast.Mult): return left * right
        if isinstance(node.op, ast.Div): return left / right
        if isinstance(node.op, ast.Pow) and right.denominator == 1 and abs(right.numerator) <= 8: return left ** right.numerator
    raise ValueError("unsupported expression")


def symbolic_equivalent(left: str, right: str) -> bool | None:
    clean = lambda value: value.strip().replace("^", "**").replace("×", "*").replace("÷", "/")
    try:
        trees = [ast.parse(clean(value), mode="eval") for value in (left, right)]
        names = sorted({node.id for tree in trees for node in ast.walk(tree) if isinstance(node, ast.Name)})
        for sample in (1, 2, 3, 5):
            values = {name: Fraction(sample + index) for index, name in enumerate(names)}
            if _safe_value(trees[0], values) != _safe_value(trees[1], values): return False
        return True
    except (SyntaxError, ValueError, ZeroDivisionError, OverflowError):
        return None


def _expressions(text: str) -> list[str]:
    return [value.strip(" .") for value in re.findall(r"(?:^|=)\s*([A-Za-z0-9().+*/^ -]+)", text) if value.strip(" .")]


def _terms(text: str) -> set[str]:
    return {word.lower() for word in WORDS.findall(text) if word.lower() not in COMMON}


def _rubric_terms(rubric: dict) -> set[str]:
    values = [str(point.get("text", "")) for point in rubric.get("markingPoints", []) if isinstance(point, dict)]
    values += [str(value) for value in rubric.get("alternatives", [])]
    return _terms(" ".join(values))


def analyze(subject_id: str, prompt: str, answer: str, rubric: dict, handwriting: dict | None = None) -> dict:
    selected = policy(subject_id)
    lower = answer.lower()
    checks: dict = {"engine": selected.name, "version": ENGINE_VERSION,
                    "dimensions": list(selected.dimensions), "signals": {}, "awardedMarks": None}
    if selected.name == "maths":
        expected = []
        for item in rubric.get("alternatives", []) + [p.get("text", "") for p in rubric.get("markingPoints", []) if isinstance(p, dict)]:
            expected.extend(_expressions(str(item)))
        student = _expressions(answer)
        equivalences = [{"student": candidate, "expected": target, "equivalent": symbolic_equivalent(candidate, target)}
                        for candidate in student[-3:] for target in expected[-3:]]
        rounding_requested = bool(re.search(r"\b(?:decimal place|significant figure|round|d\.p\.|s\.f\.)\b", prompt.lower()))
        checks["signals"] = {"symbolicEquivalence": equivalences, "showsFormula": bool(re.search(r"[A-Za-z]\s*=|=\s*[A-Za-z]", answer)),
            "showsSubstitution": bool(re.search(r"\d\s*[-+*/×÷]\s*\d|[A-Za-z]\s*=\s*-?\d", answer)),
            "hasUnits": bool(re.search(r"\b(?:mm|cm|m|km|g|kg|s|min|h|j|n|w|v|a|pa|°c|%)\b", lower)),
            "roundingRequested": rounding_requested,
            "roundingEvidence": bool(re.search(r"\b(?:decimal place|significant figure|rounded|d\.p\.|s\.f\.)\b", lower)) or
                (rounding_requested and bool(re.search(r"\d+\.\d+", answer))),
            "workingLines": len([line for line in answer.splitlines() if line.strip()])}
    elif selected.name == "science":
        rubric_terms = _rubric_terms(rubric)
        checks["signals"] = {"terminologyMatches": sorted(_terms(answer) & rubric_terms),
            "causalConnectives": re.findall(r"\b(?:because|therefore|so that|causes?|results? in|leads? to)\b", lower),
            "variables": {kind: bool(re.search(rf"\b{kind}\s+variable\b", lower)) for kind in ("independent", "dependent", "control")},
            "experimentalDetail": bool(re.search(r"\b(?:measure|repeat|average|apparatus|method|risk|accuracy|reliable)\b", lower)),
            "calculationWorking": bool(re.search(r"\d\s*[-+*/×÷=]\s*\d", answer)),
            "conclusionLanguage": bool(re.search(r"\b(?:conclude|evidence|data|trend|supports?)\b", lower))}
    elif selected.name == "ict":
        checks["signals"] = {"vocabularyMatches": sorted(_terms(answer) & _rubric_terms(rubric)),
            "scenarioReferences": len(set(re.findall(r"\b(?:user|business|school|customer|organisation|scenario)\b", lower))),
            "tradeOffLanguage": bool(re.search(r"\b(?:however|whereas|advantage|disadvantage|trade-off|on the other hand)\b", lower)),
            "linkedReasoning": len(re.findall(r"\b(?:because|therefore|so that|which means)\b", lower))}
    elif selected.name == "english":
        words = WORDS.findall(answer)
        checks["signals"] = {"taskTermMatches": sorted(_terms(answer) & _terms(prompt)),
            "evidenceMarkers": len(re.findall(r"[\"“”']|\b(?:quote|evidence|line|paragraph)\b", answer)),
            "paragraphs": len([p for p in re.split(r"\n\s*\n", answer) if p.strip()]),
            "connectives": len(re.findall(r"\b(?:however|furthermore|therefore|in contrast|consequently)\b", lower)),
            "languageVariety": round(len({word.lower() for word in words}) / len(words), 3) if words else 0}
    elif selected.name == "french":
        words = WORDS.findall(answer)
        checks["signals"] = {"comprehensionTermMatches": sorted(_terms(answer) & _terms(prompt)),
            "vocabularyVariety": round(len({word.lower() for word in words}) / len(words), 3) if words else 0,
            "wordCount": len(words),
            "accentedCharacters": len(re.findall(r"[À-ÿ]", answer)),
            "verbIndicators": len(re.findall(r"\b(?:je|tu|il|elle|nous|vous|ils|elles|ai|est|sont|vais|sera|était)\b", lower)),
            "communicationEvidence": bool(len(words) >= 3 and re.search(r"[.!?]", answer))}
    if selected.name in {"english", "french"}:
        rubric_text = " ".join(str(point.get("text", "")) for point in rubric.get("markingPoints", []) if isinstance(point, dict)).lower()
        aliases = {"task_fulfilment": ("task", "purpose", "audience"), "evidence": ("evidence", "quotation", "reference"),
            "organisation": ("organisation", "structure", "paragraph"), "language": ("language", "vocabulary", "grammar"),
            "comprehension": ("comprehension", "understand", "detail"), "vocabulary": ("vocabulary", "lexical"),
            "grammar": ("grammar", "accuracy", "tense"), "communication": ("communication", "message", "meaning")}
        checks["rubricCoverage"] = {dimension: any(word in rubric_text for word in aliases.get(dimension, (dimension,)))
                                    for dimension in selected.dimensions}
    if handwriting:
        checks["handwriting"] = handwriting
    return checks
