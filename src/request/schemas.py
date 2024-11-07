from pydantic import BaseModel


class PostBase(BaseModel):
    pass

class NewsExistsRequestModel(BaseModel):
    channel: str
    id_post: int

class NewsExistsResponseModel(BaseModel):
    exists: bool

class NewPostRequestModel(PostBase):
    channel: str
    id_post: int
    time: str
    url: str

class NewPostResponseModel(PostBase):
    pass