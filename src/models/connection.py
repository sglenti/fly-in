from pydantic import BaseModel, Field


class Connection(BaseModel):
    source_name: str
    target_name: str
    max_link_capacity: int = Field(default=1, gt=0)
    model_config = {
        'extra': 'forbid'
    }
