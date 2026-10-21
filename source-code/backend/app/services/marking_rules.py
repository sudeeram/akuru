"""Deterministic credit allocation. Model decisions are matches, never final totals."""
import re
import unicodedata
from pydantic import ValidationError
from app.errors import DomainError
from app.schemas.marking_rules import MarkingRules


def _invalid(message):
    raise DomainError("assessment_rubric_invalid", message, 409)


def validate_rules(points, maximum, rules):
    try:
        parsed = MarkingRules.model_validate(rules or {})
    except ValidationError as exc:
        _invalid("Invalid structured scoring rules: " + str(exc.errors()[0]["msg"]))
    ids = [p.get("pointId", p.get("code")) for p in points]
    if not ids or any(not i for i in ids) or len(set(ids)) != len(ids):
        _invalid("Marking-point codes must be present and unique.")
    known = set(ids)
    if any(int(p.get("maxMarks", 1)) != 1 for p in points):
        _invalid("Structured scoring currently requires one mark per distinct point.")
    for p in points:
        dependency = p.get("dependsOn")
        if dependency and (dependency not in known or dependency == p.get("pointId", p.get("code"))):
            _invalid("A marking dependency must reference a different existing point.")
    dependencies = {p.get("pointId", p.get("code")): p.get("dependsOn") for p in points}
    for start in known:
        seen = set(); node = start
        while node:
            if node in seen:
                _invalid("Marking dependencies cannot contain cycles.")
            seen.add(node); node = dependencies.get(node)
    sets = []
    for g in parsed.groups:
        if not set(g.pointIds) <= known or g.maxMarks > len(g.pointIds) or g.maxMarks > maximum:
            _invalid("A scoring group must use existing points and a valid maximum.")
        sets.append(set(g.pointIds))
    # Nested/disjoint groups give predictable hierarchical credit; arbitrary overlap is unsupported.
    for i, left in enumerate(sets):
        for right in sets[i+1:]:
            if left & right and not (left <= right or right <= left):
                _invalid("Scoring groups must be nested or disjoint; overlapping groups need manual review.")
    selective = [set(g.pointIds) for g in parsed.groups if g.maxMarks < len(g.pointIds) or g.requiredForFullCredit]
    if not parsed.groups and maximum < len(points):
        selective.append(known)
    for point in points:
        if point.get("dependsOn") and not point.get("followThrough") and any(
            {point.get("pointId", point.get("code")), point["dependsOn"]} & group for group in selective
        ):
            _invalid("Dependencies interacting with selective scoring groups need manual marking in rule version 1.")
    for combined in parsed.combinedResponses:
        if not combined.phrase.strip() or not set(combined.pointIds) <= known:
            _invalid("A combined response must have wording and reference existing points.")
    return parsed


def normalize(text):
    value = unicodedata.normalize("NFKC", text).casefold()
    return re.sub(r"\s+", " ", value).strip()


def score(decisions, points, maximum, rules, answer_text=None):
    parsed = validate_rules(points, maximum, rules)
    expected = {p["pointId"]: p for p in points}
    if len(decisions) != len(expected) or {d.pointId for d in decisions} != set(expected):
        raise DomainError("assessment_output_invalid", "AKURU did not assess every approved marking point exactly once.", 422)
    matches = {}; evidence = {}
    for d in decisions:
        p = expected[d.pointId]
        if d.criterion != p["criterion"] or d.maxMarks != p["maxMarks"] or d.marksAwarded != int(d.awarded):
            raise DomainError("assessment_output_invalid", "AKURU changed an approved marking point or returned inconsistent credit.", 422)
        if d.awarded and answer_text is not None and normalize(d.studentEvidence) not in normalize(answer_text):
            raise DomainError("assessment_output_invalid", "A matched marking point needs an exact supporting phrase from the student's answer.", 422)
        matches[d.pointId] = d.awarded
        evidence[d.pointId] = d.studentEvidence
    # Only exact, standalone approved observations earn deterministic matches. Never substring-match
    # a positive phrase inside a negation or a longer, contradictory sentence.
    clauses = {}
    if answer_text is not None:
        for raw in re.split(r"[\n;.!?]+", answer_text):
            phrase = re.sub(r"^\s*(?:[-•]|\d+[.)])\s*", "", raw).strip()
            if phrase:
                clauses[normalize(phrase)] = phrase
    if answer_text and re.search(r"\b(?:no|not|never|without|cannot|don't|doesn't|isn't|can't)\b", normalize(answer_text)):
        clauses = {}  # Leave negated/possibly contradictory answers to semantic review.
    for p in points:
        for alias in p.get("acceptedAnswers", []):
            if normalize(alias) in clauses:
                matches[p["pointId"]] = True; evidence[p["pointId"]] = clauses[normalize(alias)]
    for combined in parsed.combinedResponses:
        if normalize(combined.phrase) in clauses:
            for point_id in combined.pointIds:
                matches[point_id] = True; evidence[point_id] = clauses[normalize(combined.phrase)]
    # Remove points whose required evidence is absent, before any caps.
    for _ in points:
        for p in points:
            if p.get("dependsOn") and not p.get("followThrough") and not matches[p["dependsOn"]]:
                matches[p["pointId"]] = False
    eligible = {key for key, value in matches.items() if value}
    credited = set(eligible)
    order = {p["pointId"]: i for i, p in enumerate(points)}
    groups = sorted(parsed.groups, key=lambda g: len(g.pointIds))
    for group in groups:
        cap = group.maxMarks
        if cap and not set(group.requiredForFullCredit) <= eligible:
            cap -= 1
        selected = sorted(credited & set(group.pointIds), key=lambda key: (key not in group.requiredForFullCredit, order[key]))
        credited.difference_update(selected[cap:])
    selected = sorted(credited, key=order.get)
    credited.difference_update(selected[maximum:])
    # A dependent point cannot retain credit after its prerequisite was removed by a cap.
    for _ in points:
        for point in points:
            if point.get("dependsOn") and not point.get("followThrough") and point["dependsOn"] not in credited:
                credited.discard(point["pointId"])
    outcomes = {}
    for point in points:
        key = point["pointId"]
        complete_optional_group = any(key in g.pointIds and len(credited & set(g.pointIds)) >= g.maxMarks for g in parsed.groups)
        outcomes[key] = ("credited" if key in credited else "matched_capped" if key in eligible else
            "not_required" if len(credited) >= maximum or complete_optional_group else "missed")
    output = []
    for d in decisions:
        value = d.model_copy(deep=True)
        value.awarded = d.pointId in credited
        value.marksAwarded = int(value.awarded)
        value.studentEvidence = evidence[d.pointId]
        if matches[d.pointId] and not value.awarded:
            value.rationale += " Server scoring: matched evidence receives no additional credit after scoring limits."
        elif outcomes[d.pointId] == "not_required":
            value.rationale += " Server scoring: this alternative was not required once the available marks were earned."
        elif value.awarded and not d.awarded:
            value.rationale += " Server scoring: exact approved standalone response matched."
        output.append(value)
    return len(credited), output, {"engine": "structured-marking-v1", "matchedPointIds": sorted(eligible),
        "creditedPointIds": sorted(credited), "pointOutcomes": outcomes, "maximumMarks": maximum,
        "rules": parsed.model_dump(), "rawDecisions": [d.model_dump() for d in decisions]}


def compile_review(data):
    """Namespace part rules and impose each paper-specified subpart cap."""
    points = []; groups = []; combined = []
    for part in data.parts:
        prefix = part.label + "."
        for p in part.markingPoints:
            if len(prefix + p.code) > 30:
                _invalid("Shorten the subpart label or marking-point code before preparing official drafts (combined limit: 30 characters).")
            points.append({"code": prefix+p.code, "text": p.text, "kind": p.kind,
                "dependsOn": prefix+p.dependsOn if p.dependsOn else None,
                "followThrough": p.followThrough, "acceptedAnswers": p.acceptedAnswers})
        ids = [prefix+p.code for p in part.markingPoints]
        groups.append({"id": "part:"+part.label, "pointIds": ids, "maxMarks": part.marks})
        for g in part.scoringRules.groups:
            groups.append({"id": "group:"+prefix+g.id, "pointIds": [prefix+i for i in g.pointIds],
                "maxMarks": g.maxMarks, "requiredForFullCredit": [prefix+i for i in g.requiredForFullCredit]})
        for c in part.scoringRules.combinedResponses:
            combined.append({"phrase": c.phrase, "pointIds": [prefix+i for i in c.pointIds]})
    rules = {"version":1,"groups":groups,"combinedResponses":combined}
    rules = validate_rules(points, data.marks, rules).model_dump()
    return points, rules
