from dataclasses import dataclass, field
from .provider import Provider

@dataclass
class Template:
    user_prompt: str 
    system_prompt: str = ''

    provider: Provider = None
    cmd: Command = None
    test: dict = field(default_factory=dict)
