from fastapi import APIRouter, Request, Depends, Query, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Article, User, Settings
from app.database import get_db
from fastapi.templating import Jinja2Templates
import math
import logging
from app.user import get_current_user  # hoặc từ auth nếu định nghĩa ở đó
from typing import Optional

router = APIRouter()
templates = Jinja2Templates(directory="ux/templates/admin")
logging.basicConfig(level=logging.DEBUG)


class Pagination:
    def __init__(self, page, per_page, total):
        self.page = page
        self.per_page = per_page
        self.total = total

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page * self.per_page < self.total

    @property
    def prev_num(self):
        return self.page - 1

    @property
    def next_num(self):
        return self.page + 1

    def iter_pages(self, left_edge=2, left_current=2, right_current=2, right_edge=2):
        total_pages = math.ceil(self.total / self.per_page)
        last = 0
        for num in range(1, total_pages + 1):
            if (num <= left_edge or 
               (self.page - left_current <= num <= self.page + right_current) or 
               num > total_pages - right_edge):
                if last + 1 != num:
                    yield None
                yield num
                last = num


# Dependency kiểm tra phân quyền admin
def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user or current_user.Role.lower() != "admin":
        raise HTTPException(
            status_code=403,
            detail="Truy cập bị từ chối: chỉ admin mới được phép"
        )
    return current_user


# 1. Trang quản trị tổng (baseAdmin)
@router.get("/admin", response_class=HTMLResponse)
async def admin_home(
    request: Request,
    current_user: User = Depends(require_admin)
):
    return templates.TemplateResponse("baseAdmin.html", {"request": request, "user": current_user})


# 2. Quản lý bài viết (list có filter, phân trang)
@router.get("/admin/1", response_class=HTMLResponse)
async def manage_articles(
    request: Request, 
    db: Session = Depends(get_db),
    page: int = Query(1, alias="page", ge=1),
    per_page: int = 10,
    category: str = "",
    status: str = "",
    query_text: str = "",
    current_user: User = Depends(require_admin)
):
    article_query = db.query(Article)
    if category:
        article_query = article_query.filter(Article.type == category)
    if status:
        article_query = article_query.filter(Article.status == status)
    if query_text:
        article_query = article_query.filter(Article.title.ilike(f"%{query_text}%"))
    total_articles = article_query.count()
    articles = article_query.order_by(Article.date_posted.desc()) \
        .offset((page - 1) * per_page) \
        .limit(per_page) \
        .all()
    pagination = Pagination(page, per_page, total_articles)
    categories = [cat[0] for cat in db.query(Article.type).distinct().all()]
    return templates.TemplateResponse(
        "QLBaiViet.html",
        {
            "request": request,
            "articles": articles,
            "pagination": pagination,  
            "categories": categories,
            "selected_category": category,
            "selected_status": status,
            "search_query": query_text,
            "user": current_user
        }
    )


# 3. Xóa bài viết
@router.delete("/admin/delete_article/{article_id}")
async def delete_article(article_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    article = db.query(Article).filter(Article.article_id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Bài viết không tồn tại")
    db.delete(article)
    db.commit()
    return {"message": "Xóa bài viết thành công"}


# 4. Quản lý người dùng
@router.get("/admin/2", response_class=HTMLResponse)
async def manage_users(
    request: Request, 
    db: Session = Depends(get_db),
    role: str = "",
    status: str = "",
    query: str = "",
    current_user: User = Depends(require_admin)
):
    users_query = db.query(User)
    if role:
        users_query = users_query.filter(User.Role == role)
    if status:
        if status.lower() == "active":
            users_query = users_query.filter(User.Status == "Active")
        elif status.lower() == "inactive":
            users_query = users_query.filter(User.Status == "Inactive")
    if query:
        search_term = f"%{query}%"
        users_query = users_query.filter(User.FirstName.ilike(search_term) | User.Email.ilike(search_term))
    users = users_query.order_by(User.ID).all()
    roles = db.query(User.Role).distinct().all()
    roles = [r[0] for r in roles]
    return templates.TemplateResponse(
        "QLNguoiDung.html", 
        {
            "request": request,
            "users": users,
            "roles": roles,
            "user": current_user
        }
    )


# 5. Xóa người dùng
@router.delete("/admin/delete_user/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    user_to_delete = db.query(User).filter(User.ID == user_id).first()
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="Người dùng không tồn tại")
    db.delete(user_to_delete)
    db.commit()
    return {"message": "Xóa người dùng thành công"}


# 6. Đổi trạng thái kích hoạt người dùng
@router.put("/admin/toggle_user_status/{user_id}")
async def toggle_user_status(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    user_to_update = db.query(User).filter(User.ID == user_id).first()
    if not user_to_update:
        raise HTTPException(status_code=404, detail="Người dùng không tồn tại")
    if user_to_update.Status == "Active":
        user_to_update.Status = "Inactive"
    else:
        user_to_update.Status = "Active"
    db.commit()
    return {"message": "Cập nhật trạng thái thành công", "new_status": user_to_update.Status}


# 7. Duyệt yêu cầu đăng ký tác giả của người dùng
@router.put("/admin/approve_author_request/{user_id}")
async def approve_author_request(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    user_to_update = db.query(User).filter(User.ID == user_id).first()
    if not user_to_update:
        raise HTTPException(status_code=404, detail="Người dùng không tồn tại")
    if not user_to_update.author_requested:
        raise HTTPException(status_code=400, detail="Không có yêu cầu đăng ký tác giả nào")
    user_to_update.Role = "author"
    user_to_update.author_requested = False
    db.commit()
    return {"message": "User role changed to author"}


# 8. Hủy yêu cầu đăng ký tác giả
@router.put("/admin/clear_author_request/{user_id}")
async def clear_author_request(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    user_to_update = db.query(User).filter(User.ID == user_id).first()
    if not user_to_update:
        raise HTTPException(status_code=404, detail="Người dùng không tồn tại")
    if not user_to_update.author_requested:
        raise HTTPException(status_code=400, detail="Không có yêu cầu đăng ký tác giả nào")
    user_to_update.author_requested = False
    db.commit()
    return {"message": "Author request removed"}

# Endpoint 9: Lấy danh sách bài viết Pending (dành cho duyệt bài)
@router.get("/admin/3", response_class=HTMLResponse)
async def pending_articles(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    # Lấy bài viết có trạng thái "Pending" (theo định nghĩa hệ thống của bạn)
    pending_articles = db.query(Article)\
                         .filter(Article.status == "Pending")\
                         .order_by(Article.date_posted.desc()).all()
    
    return templates.TemplateResponse(
        "QLDuyetBaiViet.html",
        {
            "request": request,
            "pending_articles": pending_articles,
            "user": current_user,
        }
    )


# Endpoint 10: Phê duyệt bài viết (chuyển trạng thái từ Pending sang published)
@router.post("/admin/approve_article/{article_id}")
async def approve_article(
    article_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    article = db.query(Article)\
                .filter(Article.article_id == article_id, Article.status == "Pending")\
                .first()
    if not article:
        raise HTTPException(
            status_code=404, 
            detail="Bài viết không tồn tại hoặc không ở trạng thái chờ duyệt"
        )
    article.status = "published"
    db.commit()
    return {"message": "Bài viết đã được phê duyệt và chuyển sang trạng thái published", "new_status": article.status}


@router.post("/admin/reject_article/{article_id}")
async def reject_article(
    article_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    article = db.query(Article)\
                .filter(Article.article_id == article_id, Article.status == "Pending")\
                .first()
    if not article:
        raise HTTPException(
            status_code=404, 
            detail="Bài viết không tồn tại hoặc không ở trạng thái chờ duyệt"
        )
    article.status = "rejected"
    db.commit()
    return {"message": "Bài viết đã bị từ chối"}

# 11. Thống kê báo cáo
@router.get("/admin/4", response_class=HTMLResponse)
async def statistics(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    article_stats = db.query(
        func.year(Article.date_posted).label('year'),
        func.month(Article.date_posted).label('month'),
        func.count(Article.article_id).label('count')
    ).group_by(func.year(Article.date_posted), func.month(Article.date_posted)) \
     .order_by(func.year(Article.date_posted), func.month(Article.date_posted)) \
     .all()

    article_stats_json = [
        {"month": f"{row.year}-{row.month:02d}", "count": row.count} for row in article_stats
    ]

    user_stats = db.query(
        func.year(User.RegistrationDate).label('year'),
        func.month(User.RegistrationDate).label('month'),
        func.count(User.ID).label('count')
    ).group_by(func.year(User.RegistrationDate), func.month(User.RegistrationDate)) \
     .order_by(func.year(User.RegistrationDate), func.month(User.RegistrationDate)) \
     .all()

    user_stats_json = [
        {"month": f"{row.year}-{row.month:02d}", "count": row.count} for row in user_stats
    ]

    return templates.TemplateResponse(
        "QLBaoCaoThongKe.html",
        {
            "request": request,
            "article_stats": article_stats_json,
            "user_stats": user_stats_json,
            "user": current_user
        }
    )


# 12. Trang cài đặt hệ thống (GET và POST)
@router.get("/admin/5", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    settings = {}
    db_settings = db.query(Settings).all()
    for setting in db_settings:
        settings[setting.setting_key] = setting.value
    return templates.TemplateResponse(
        "QLHeThong.html",
        {
            "request": request,
            "settings": settings,
            "user": current_user
        }
    )

@router.post("/admin/5")
async def save_settings(
    db: Session = Depends(get_db),
    system_name: str = Form(...),
    timezone: str = Form(...),
    smtp_server: str = Form(...),
    email_from: str = Form(...),
    current_user: User = Depends(require_admin)
):
    settings_data = {
        "system_name": system_name,
        "timezone": timezone,
        "smtp_server": smtp_server,
        "email_from": email_from
    }
    for key, value in settings_data.items():
        setting = db.query(Settings).filter(Settings.setting_key == key).first()
        if setting:
            setting.value = value
        else:
            db.add(Settings(setting_key=key, value=value))
    db.commit()
    return {"message": "Cài đặt đã được lưu thành công"}