from pydantic import BaseModel, model_validator

from app.utils.validate_helpers import sanitize_input


class CleanableBaseModel(BaseModel):
    @model_validator(mode="before")
    @classmethod
    def sanitize_strings(cls, values: dict) -> dict:
        for key, val in values.items():
            if isinstance(val, str):
                values[key] = sanitize_input(val)
        return values
