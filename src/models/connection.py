from pydantic import BaseModel, Field


class Connection(BaseModel):
    end_point1: str
    end_point2: str
    max_link_capacity: int = Field(default=1, gt=0)
    model_config = {
        'extra': 'forbid',
        'frozen': True
    }
