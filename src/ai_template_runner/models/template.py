from dataclasses import dataclass, field
from ..command import Command
from .provider import Provider

@dataclass
class Template:
    user_prompt: str 
    system_prompt: str = ''

    provider: Provider = None
    cmd: Command = None
    test: dict = field(default_factory=dict)
    out: dict = field(default_factory=dict)
