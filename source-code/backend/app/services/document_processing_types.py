from dataclasses import dataclass


@dataclass
class ProcessingFailure(Exception):
    code: str
    message: str
