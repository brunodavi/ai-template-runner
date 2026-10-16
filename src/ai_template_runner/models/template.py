from dataclasses import dataclass, field

@dataclass
class TemplateConfig:
    name: str | None = None
    description: str | None = None

    temperature: int | None = None
    top_k: int | None = None
    top_p: int | None = None

@dataclass
class Template:
    prompt: str
    config: TemplateConfig = field(default_factory=TemplateConfig)
