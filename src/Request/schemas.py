from typing import  List

from fastapi import UploadFile, File
from pydantic import BaseModel
from datetime import datetime


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
    time: datetime
    url: str
    images: List[UploadFile] = File(None)
    videos: List[UploadFile] = File(None)


class NewPostResponseModel(PostBase):
    pass