"""Versioned, finite selections only: never accept uploaded SVG or image URLs."""
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, StrictStr, model_validator, ValidationError

CATALOGUE = json.loads((Path(__file__).parents[1] / 'resources' / 'student-avatar-v1.json').read_text())


class StudentAvatarConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')
    version: Literal[1]
    base: StrictStr
    face: StrictStr
    skin: StrictStr
    hair: StrictStr
    hairColor: StrictStr
    eyes: StrictStr
    eyeColor: StrictStr
    brows: StrictStr
    mouth: StrictStr
    outfit: StrictStr
    clothesColor: StrictStr
    glasses: StrictStr
    background: StrictStr

    @model_validator(mode='before')
    @classmethod
    def strict_version(cls, value):
        if isinstance(value, dict) and type(value.get('version')) is not int:
            raise ValueError('Avatar version must be an integer')
        return value

    @model_validator(mode='after')
    def known_parts(self):
        for field, choices in CATALOGUE['options'].items():
            if getattr(self, field) not in choices:
                raise ValueError(f'Unsupported avatar option: {field}')
        if self.hair not in CATALOGUE['hairByBase'][self.base]:
            raise ValueError('Hairstyle must match the starting character')
        return self


class StudentAvatarResponse(BaseModel):
    avatar: StudentAvatarConfig | None


def public_avatar(value: object) -> dict | None:
    if value is None:
        return None
    # Preserve older saved avatars while adapting their hairstyle to the base.
    # New writes still use strict validation above; no stored records are rewritten.
    if (
        isinstance(value, dict)
        and isinstance(value.get('base'), str)
        and isinstance(value.get('hair'), str)
        and value['base'] in CATALOGUE['hairByBase']
        and value['hair'] in CATALOGUE['options']['hair']
    ):
        if value['hair'] not in CATALOGUE['hairByBase'][value['base']]:
            preset = next(p for p in CATALOGUE['presets'] if p['base'] == value['base'])
            value = {**value, 'hair': preset['hair']}
    try:
        return StudentAvatarConfig.model_validate(value).model_dump()
    except ValidationError:
        # Older/unsupported records must fall back to initials rather than break profiles.
        return None
