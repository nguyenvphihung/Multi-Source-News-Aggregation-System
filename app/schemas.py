from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ArticleBase(BaseModel):
    article_id: str
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    date_posted: datetime
    author: Optional[str] = None
    source_url: Optional[str] = None
    status: Optional[str] = None
    type: Optional[str] = None
    image_urls: Optional[str] = None
    video_urls: Optional[str] = None

    class Config:
        from_attributes = True

# Schema dùng cho các thao tác tạo, cập nhật người dùng (mật khẩu có trong request)
class UserBase(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    newsletter: Optional[bool] = False
    terms_accepted: Optional[bool] = False
    role: Optional[str] = "User"
    status: Optional[str] = "Active"
    registration_date: Optional[datetime] = None
    avatar_url: Optional[str] = None 
    author_requested: Optional[bool] = False

    class Config:
        from_attributes = True


# Schema dành cho phản hồi dữ liệu người dùng (không bao gồm password)
class UserOut(UserBase):
    pass

# Schema dùng khi đăng ký: Password được yêu cầu
class UserCreate(UserBase):
    password: str

# Schema dùng khi cập nhật người dùng, Password là tùy chọn.
class UserUpdate(UserBase):
    password: Optional[str] = None

class SettingsBase(BaseModel):
    setting_key: str
    value: str

    class Config:
        from_attributes = True

class ArticleCreate(ArticleBase):
    pass

class ArticleUpdate(ArticleBase):
    pass

class SettingsCreate(SettingsBase):
    pass

class SettingsUpdate(SettingsBase):
    pass