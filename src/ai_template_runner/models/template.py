from dataclasses import dataclass, field
from .provider import Provider

@dataclass
class Template:
    provider: Provider
    user_prompt: str
    system_prompt: str = ''
