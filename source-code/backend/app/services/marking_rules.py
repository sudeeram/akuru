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
    band_ids = {b.pointId for g in parsed.scoreBands for b in g.bands}
    weights = {b.pointId: b.marks for g in parsed.scoreBands for b in g.bands}
    for band in parsed.scoreBands:
        if not {b.pointId for b in band.bands} <= known or any(b.marks > maximum for b in band.bands):
            _invalid("Score bands must reference existing points and not exceed the question maximum.")
        if len({b.marks for b in band.bands}) != len(band.bands):
            _invalid("Use one criterion per distinct score band; put equivalent answers in that criterion.")
    if any((p.get("dependsOn") or p.get("followThrough")) for p in points) and band_ids:
        _invalid("Score bands with dependencies or follow-through require manual review.")
    if any(set(c.pointIds) & band_ids for c in parsed.combinedResponses):
        _invalid("Combined responses cannot override score-band criteria.")
    sets = []
    for g in parsed.groups:
        if not set(g.pointIds) <= known or g.maxMarks > sum(weights.get(i, 1) for i in g.pointIds) or g.maxMarks > maximum:
            _invalid("A scoring group must use existing points and a valid maximum.")
        for band in parsed.scoreBands:
            ids_in_band = {b.pointId for b in band.bands}
            if ids_in_band & set(g.pointIds) and (not ids_in_band <= set(g.pointIds) or g.requiredForFullCredit or g.maxMarks < max(b.marks for b in band.bands)):
                _invalid("A scoring group must contain an entire score-band group, without conditional full-credit rules.")
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
        if d.awarded and answer_text is not None and (not normalize(d.studentEvidence) or normalize(d.studentEvidence) not in normalize(answer_text)):
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
    band_ids = {b.pointId for g in parsed.scoreBands for b in g.bands}
    for p in points:
        if p["pointId"] in band_ids:
            continue  # A numeric alias alone cannot establish rounding/method/exclusion criteria.
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
    if parsed.scoreBands:
        return _score_bands(decisions, points, maximum, parsed, matches, evidence, order)
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


def _score_bands(decisions, points, maximum, parsed, matches, evidence, order):
    weights = {p["pointId"]: 1 for p in points}
    eligible = {key for key, value in matches.items() if value}
    credited = set(eligible)
    selected_bands = {}
    for group in parsed.scoreBands:
        ids = {b.pointId for b in group.bands}
        weights.update({b.pointId: b.marks for b in group.bands})
        matched = [b for b in group.bands if b.pointId in eligible]
        winner = max(matched, key=lambda b: b.marks) if matched else None
        credited.difference_update(ids)
        if winner:
            credited.add(winner.pointId)
        selected_bands[group.id] = winner.pointId if winner else None
    # Bands are atomic: caps may remove a band but never manufacture a partial band.
    limits = [(set(g.pointIds), g.maxMarks, g.requiredForFullCredit)
              for g in sorted(parsed.groups, key=lambda g: len(g.pointIds))]
    limits.append((set(weights), maximum, []))
    for ids, cap, required in limits:
        if cap and not set(required) <= eligible:
            cap -= 1
        used = 0
        for key in sorted(credited & ids, key=lambda k: (k not in required, order[k])):
            if used + weights[key] <= cap:
                used += weights[key]
            else:
                credited.remove(key)
    total = sum(weights[k] for k in credited)
    output = []
    outcomes = {}
    for d in decisions:
        value = d.model_copy(deep=True)
        value.maxMarks = weights[d.pointId]
        value.awarded = d.pointId in credited
        value.marksAwarded = weights[d.pointId] if value.awarded else 0
        value.studentEvidence = evidence[d.pointId]
        outcomes[d.pointId] = "credited" if value.awarded else "matched_capped" if d.pointId in eligible else "not_required" if total >= maximum else "missed"
        value.rationale += " Server scoring: only the highest matched band earns credit; alternative bands are not additive."
        output.append(value)
    return total, output, {"engine": "structured-marking-v2", "matchedPointIds": sorted(eligible),
        "creditedPointIds": sorted(credited), "selectedBands": selected_bands, "pointOutcomes": outcomes,
        "maximumMarks": maximum, "rules": parsed.model_dump(), "rawDecisions": [d.model_dump() for d in decisions]}


def expected_marks(ids, rules):
    """Marks for an Admin's expected credited IDs, rejecting additive alternative bands."""
    parsed = MarkingRules.model_validate(rules)
    weights = {b.pointId: b.marks for g in parsed.scoreBands for b in g.bands}
    if any(len(set(ids) & {b.pointId for b in g.bands}) > 1 for g in parsed.scoreBands):
        _invalid("Expected credit must select only one band per score-band group.")
    return sum(weights.get(i, 1) for i in ids)


def compile_review(data):
    """Namespace part rules and impose each paper-specified subpart cap."""
    points = []; groups = []; combined = []; bands = []
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
        for g in part.scoringRules.scoreBands:
            bands.append({"id": "band:"+prefix+g.id, "bands": [
                {"pointId": prefix+b.pointId, "marks": b.marks} for b in g.bands]})
        for c in part.scoringRules.combinedResponses:
            combined.append({"phrase": c.phrase, "pointIds": [prefix+i for i in c.pointIds]})
    rules = {"version":2 if bands else 1,"groups":groups,"combinedResponses":combined}
    deterministic_parts = [p for p in data.parts if p.scoringRules.deterministic]
    if deterministic_parts:
        if len(deterministic_parts) != len(data.parts):
            _invalid("Mixed semantic/deterministic subparts must be prepared as separate assessment items; do not discard deterministic certificates.")
        matchers = []
        contexts = []
        for part in deterministic_parts:
            contexts.append(dict(label=part.label, marks=part.marks, prompt=part.prompt,
                markingPoints=[p.model_dump(mode='json') for p in part.markingPoints],
                scoringRules=part.scoringRules.model_dump(mode='json')))
            for matcher in part.scoringRules.deterministic.matchers:
                value = matcher.model_dump(mode='json')
                value.update(pointId=part.label+'.'+matcher.pointId,
                    answerKey=part.label+('.'+matcher.answerKey if matcher.answerKey else ''))
                matchers.append(value)
        rules.update(version=3, deterministic=dict(engine='deterministic-v1', matchers=matchers, parts=contexts))
    if bands:
        rules["scoreBands"] = bands
    rules = validate_rules(points, data.marks, rules).model_dump()
    return points, rules
