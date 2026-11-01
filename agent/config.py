from dotenv import load_dotenv
import os
import sys
from dataclasses import dataclass, field

@dataclass
class Config:
    OPENAI_BASE_URL: str
    MODEL: str
    DATA_BASE_URL: str
    OPENAI_API_KEY: str = field(repr=False)



def load_config(): 
    load_dotenv()

    names = ["OPENAI_BASE_URL", "MODEL", "OPENAI_API_KEY", "DATA_BASE_URL"]
    values = {name: os.getenv(name) for name in names}
    missing = [name for name, value in values.items() if not value]
    if missing:
        sys.exit(f"Missing environment variable(s): {', '.join(missing)}")

    # Strip trailing slashes: the URLs are joined with "/" later, and a "//" can cause a 404
    values["OPENAI_BASE_URL"] = values["OPENAI_BASE_URL"].rstrip("/")
    values["DATA_BASE_URL"] = values["DATA_BASE_URL"].rstrip("/")

    return Config(**values)
    

