import subprocess

class Command:
    def __init__(self, **kwargs):
        self.commands = kwargs

    def __getattr__(self, name):
        command = self.commands[name]
        return subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True
        ).stdout.strip()
