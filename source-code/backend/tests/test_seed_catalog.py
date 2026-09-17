from app.seed_catalog import COURSES, SUBJECTS, TUTOR_AVATARS, TUTOR_VOICES


def test_catalogue_seed_is_complete_and_has_unique_keys():
    assert [row["id"] for row in COURSES] == ["iprimary", "ilower-secondary", "igcse"]
    assert next(row for row in COURSES if row["id"] == "igcse")["phase1_active"] is True
    assert {row["id"] for row in SUBJECTS} == {
        "english", "maths", "ict", "biology", "chemistry", "physics", "french", "human-biology",
    }
    assert len({row["code"] for row in TUTOR_AVATARS}) == len(TUTOR_AVATARS) == 5
    assert len({row["code"] for row in TUTOR_VOICES}) == len(TUTOR_VOICES) == 3
