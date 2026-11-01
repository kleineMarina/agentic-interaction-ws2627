import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


class RunLogger:
    def __init__(self, model):
        self.model = model
        self.run_id = uuid.uuid4().hex
        self.folder = Path(__file__).parent.parent / 'logs'
        self.folder.mkdir(exist_ok=True) # exist_ok=True --> no error if folder already exists
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H-%M-%S')
        self.file_name = f'{timestamp}_{self.run_id}.jsonl'
        self.path = self.folder / self.file_name

    def log(self, event, tool=None, args=None, ok=None, duration_ms=None, error=None):
        entry = {
            'ts': datetime.now(timezone.utc).isoformat(),
            'run_id': self.run_id,
            'event': event,
            'tool': tool,
            'args': args,
            'ok': ok,
            'model': self.model,
            'duration_ms': duration_ms,
            'error': error,
        }

        with open(self.path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')