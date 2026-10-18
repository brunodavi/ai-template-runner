import json
import urllib.request

from .models.provider import Provider


def post_json(url, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=180) as response:
        return json.loads(response.read())


def llamacpp(
        provider: Provider,
        user_prompt: str,
        system_prompt: str = '',
    ):

    url = provider.base_url

    payload = {
        "model": provider.model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": provider.temperature,
        "top_p": provider.top_p,
        "top_k": provider.top_k,
        "min_p": provider.min_p,

        "max_tokens": provider.max_tokens,
        "seed": provider.seed,
        "stop": provider.stop,

        "frequency_penalty": provider.frequency_penalty,
        "presence_penalty": provider.presence_penalty,
        "repeat_penalty": provider.repeat_penalty,

        "stream": False,

        **provider.extras,
    }

    return post_json(url, payload)
