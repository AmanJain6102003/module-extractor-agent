from pydantic import BaseModel, validator
from typing import Dict, List, Any

class ModuleModel(BaseModel):
    module: str
    Description: str
    Submodules: Dict[str, str]

def validate_modules(data: List[Any]):
    # ensure final structure is a list of objects matching ModuleModel and no extra keys
    if not isinstance(data, list):
        raise ValueError("Output must be a list of module objects")
    cleaned = []
    for item in data:
        m = ModuleModel(**item)
        # pydantic will raise on wrong types
        cleaned.append({'module': m.module, 'Description': m.Description, 'Submodules': m.Submodules})
    return cleaned
