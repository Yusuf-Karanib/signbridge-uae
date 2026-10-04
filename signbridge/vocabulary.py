from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from signbridge.config import VOCABULARY_PATH


@dataclass(frozen=True)
class SignDefinition:
    id: str
    gloss: str
    output: str
    reference_url: str = ""


@dataclass(frozen=True)
class LanguagePack:
    id: str
    name: str
    short_name: str
    output_language: str
    locale: str
    direction: str
    reference_name: str
    reference_url: str
    signs: tuple[SignDefinition, ...]

    @property
    def sign_ids(self) -> tuple[str, ...]:
        return tuple(sign.id for sign in self.signs)

    def sign_for_id(self, sign_id: str) -> SignDefinition:
        for sign in self.signs:
            if sign.id == sign_id:
                return sign
        raise KeyError(f"Unknown sign id for {self.id}: {sign_id}")


class Vocabulary:
    def __init__(self, packs: dict[str, LanguagePack], scope_notice: str):
        self.packs = packs
        self.scope_notice = scope_notice

    @classmethod
    def load(cls, path: Path = VOCABULARY_PATH) -> "Vocabulary":
        payload = json.loads(path.read_text(encoding="utf-8"))
        packs: dict[str, LanguagePack] = {}
        for language_id, raw in payload["languages"].items():
            signs = tuple(SignDefinition(**item) for item in raw["signs"])
            if len(signs) != 4:
                raise ValueError(f"{language_id} must contain exactly 4 signs")
            ids = [sign.id for sign in signs]
            if len(ids) != len(set(ids)):
                raise ValueError(f"Duplicate sign id in {language_id}")
            packs[language_id] = LanguagePack(
                id=language_id,
                name=raw["name"],
                short_name=raw["short_name"],
                output_language=raw["output_language"],
                locale=raw["locale"],
                direction=raw["direction"],
                reference_name=raw["reference_name"],
                reference_url=raw["reference_url"],
                signs=signs,
            )
        return cls(packs=packs, scope_notice=payload["scope_notice"])

    def pack(self, language_id: str) -> LanguagePack:
        return self.packs[language_id]

