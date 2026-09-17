from sqlalchemy.orm import Session

from app.database import engine
from app.models import Course, Subject, TutorAvatar, TutorVoicePreset


COURSES = (
    {"id": "iprimary", "name": "iPrimary", "phase1_active": False},
    {"id": "ilower-secondary", "name": "iLower Secondary", "phase1_active": False},
    {"id": "igcse", "name": "iGCSE", "phase1_active": True},
)

SUBJECTS = (
    {"id": "english", "name": "English"},
    {"id": "maths", "name": "Maths"},
    {"id": "ict", "name": "ICT"},
    {"id": "biology", "name": "Biology"},
    {"id": "chemistry", "name": "Chemistry"},
    {"id": "physics", "name": "Physics"},
    {"id": "french", "name": "French"},
    {"id": "human-biology", "name": "Human Biology"},
)

TUTOR_AVATARS = (
    {"code": "akuru-atlas", "display_name": "Atlas", "description": "A confident idea hero for structured challenges.", "image_path": "/akuru-bots/akuru-bot-idea.png", "presentation": "masculine", "is_enabled": True, "sort_order": 10},
    {"code": "akuru-nova", "display_name": "Nova", "description": "A thoughtful reading hero who explains with care.", "image_path": "/akuru-bots/akuru-bot-reader.png", "presentation": "feminine", "is_enabled": True, "sort_order": 20},
    {"code": "akuru-spark", "display_name": "Spark", "description": "An upbeat learning hero who celebrates progress.", "image_path": "/akuru-bots/akuru-bot-celebrate.png", "presentation": "neutral", "is_enabled": True, "sort_order": 30},
    {"code": "akuru-orbit", "display_name": "Orbit", "description": "A curious hero for questions and discoveries.", "image_path": "/akuru-bots/akuru-bot-curious.png", "presentation": "neutral", "is_enabled": True, "sort_order": 40},
    {"code": "akuru-byte", "display_name": "Byte", "description": "A focused technology hero for worked examples.", "image_path": "/akuru-bots/akuru-bot-laptop.png", "presentation": "masculine", "is_enabled": True, "sort_order": 50},
)

TUTOR_VOICES = (
    {"code": "clear-coach", "display_name": "Clear coach", "description": "A clear, steady masculine presentation.", "provider_voice_ref": None, "presentation": "masculine", "is_enabled": True, "sort_order": 10},
    {"code": "warm-guide", "display_name": "Warm guide", "description": "A warm, patient feminine presentation.", "provider_voice_ref": None, "presentation": "feminine", "is_enabled": True, "sort_order": 20},
    {"code": "bright-companion", "display_name": "Bright companion", "description": "A lively neutral presentation.", "provider_voice_ref": None, "presentation": "neutral", "is_enabled": True, "sort_order": 30},
)


def _upsert(session: Session, model, key: str, values: dict) -> None:
    row = session.get(model, values[key])
    if row is None:
        session.add(model(**values))
        return
    for field, value in values.items():
        if field != key:
            setattr(row, field, value)


def seed(session: Session) -> None:
    for values in COURSES:
        _upsert(session, Course, "id", values)
    for values in SUBJECTS:
        _upsert(session, Subject, "id", values)
    for values in TUTOR_AVATARS:
        _upsert(session, TutorAvatar, "code", values)
    for values in TUTOR_VOICES:
        _upsert(session, TutorVoicePreset, "code", values)
    session.commit()


def main() -> None:
    with Session(engine) as session:
        seed(session)
    print("AKURU catalogue and Tutor presets are ready.")


if __name__ == "__main__":
    main()
