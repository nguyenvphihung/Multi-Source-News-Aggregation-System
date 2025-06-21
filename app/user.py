from fastapi import APIRouter, Request, Depends, Query, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from app.models import Article, User
from app.database import get_db
from fastapi.templating import Jinja2Templates
from app.utils import process_images, get_first_image
import math
from typing import Optional
from app.schemas import ArticleCreate

router = APIRouter()
templates = Jinja2Templates(directory="templates/")

# Lấy danh mục từ bài viết
def get_base_categories(db: Session):
    categories_query = db.query(Article.type).distinct().all()
    mapping = {
        "nhip-song-tre": "Nhịp sống trẻ",
        "thoi-su": "Thời sự",
        "xe": "Xe",
        "kinh-doanh": "Kinh doanh",
        "giai-tri": "Giải trí",
        "the-thao": "Thể thao",
        "chinh-tri": "Chính trị",
        "phap-luat": "Pháp luật",
        "suc-khoe": "Sức khỏe",
        "van-hoa": "Văn hóa",
        "cong-nghe": "Công nghệ",
        "du-lich": "Du lịch",
        "am-nhac": "Âm nhạc",
        "giao-duc": "Giáo dục",
        "the-gioi": "Thế giới",
        "kinh-te-ky-thuat": "Kinh tế & Kỹ thuật",
    }
    
    categories = []
    for cat in categories_query:
        slug = cat[0].lower()
        name = mapping.get(slug, slug.replace("-", " ").title())
        categories.append({"slug": slug, "name": name})
    
    return {
        "topbar_categories": categories,
        "navbar_categories": categories,
        "footer_categories": categories,
    }

# Dependency: Xác thực người dùng qua cookie "user_email"
async def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    Email = request.cookies.get("user_email")
    if Email:
        user = db.query(User).filter(User.email == Email).first()
        return user
    return None

# Dependency: Kiểm tra quyền Author hoặc Admin (cho trang upload bài)
def check_author_or_admin(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Bạn chưa đăng nhập.")
    db_user = db.query(User).filter(User.email == current_user.email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Người dùng không tồn tại.")
    if db_user.role.lower() not in ["author", "admin"]:
        raise HTTPException(status_code=403, detail="Bạn không phải Author hoặc Admin. Không thể truy cập.")
    return db_user

# Trang chủ
@router.get("/", response_class=HTMLResponse)
@router.get("/home", response_class=HTMLResponse)
async def home(
    request: Request, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    featured_post = db.query(Article).filter(Article.status=="published")\
                         .order_by(Article.date_posted.desc()).first()
    if featured_post:
        featured_post.image_urls = get_first_image(featured_post.image_urls) if featured_post.image_urls else ""
    popular_posts = db.query(Article).filter(Article.status=="published")\
                        .order_by(Article.date_posted.desc()).limit(5).all()
    latest_posts = db.query(Article).filter(Article.status=="published")\
                       .order_by(Article.date_posted.desc()).limit(8).all()
    base_categories = get_base_categories(db)
    
    return templates.TemplateResponse(
        "user/home.html",
        {
            "request": request,
            "featured_post": featured_post,
            "popular_posts": process_images(popular_posts),
            "latest_posts": process_images(latest_posts),
            "user": current_user,
            **base_categories,
        }
    )

# Trang danh mục
@router.get("/category/{category}", response_class=HTMLResponse)
async def get_category(
    request: Request, 
    category: str, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    category_posts = db.query(Article).filter(Article.type == category, Article.status == "published").order_by(Article.date_posted.desc()).all()
    
    if not category_posts:
        raise HTTPException(status_code=404, detail="Không có bài viết nào trong danh mục này.")

    # Lấy danh sách danh mục từ get_base_categories
    base_categories = get_base_categories(db)

    # Tìm tên danh mục dựa trên slug
    category_name = next(
        (cat["name"] for cat in base_categories["navbar_categories"] if cat["slug"] == category),
        category.replace("-", " ").title()  # Nếu không tìm thấy, mặc định format slug
    )

    return templates.TemplateResponse(
        "user/category.html",
        {
            "request": request,
            "category_slug": category,  # Vẫn giữ slug nếu cần
            "category_name": category_name,  # Truyền tên danh mục đầy đủ
            "category_posts": process_images(category_posts),
            "user": current_user,
            **base_categories,
        }
    )

# Trang chi tiết bài viết
@router.get("/news_detail/{article_id}", response_class=HTMLResponse, name="news_detail")
async def news_detail(
    request: Request, 
    article_id: str, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    article = db.query(Article).filter(Article.article_id==article_id, Article.status=="published").first()
    if not article:
        raise HTTPException(status_code=404, detail="Bài viết không tồn tại hoặc chưa được xuất bản")
    base_categories = get_base_categories(db)
    return templates.TemplateResponse(
        "user/news_detail.html",
        {
            "request": request,
            "article": article,
            "user": current_user,
            **base_categories,
        }
    )

# Trang tất cả bài viết với phân trang
@router.get("/all_posts", response_class=HTMLResponse, name="all_posts")
async def all_posts(
    request: Request, 
    db: Session = Depends(get_db),
    page: int = Query(1, alias="page", ge=1),
    per_page: int = 10,
    current_user: Optional[User] = Depends(get_current_user)
):
    total_posts = db.query(Article).filter(Article.status=="published").count()
    posts = db.query(Article).filter(Article.status=="published")\
              .order_by(Article.date_posted.desc()) \
              .offset((page - 1) * per_page) \
              .limit(per_page) \
              .all()
    base_categories = get_base_categories(db)
    return templates.TemplateResponse(
        "user/all_post.html",
        {
            "request": request,
            "all_posts": process_images(posts),
            "page": page,
            "total_pages": math.ceil(total_posts / per_page),
            "user": current_user,
            **base_categories,
        }
    )



# Trang tìm kiếm bài viết
POSTS_PER_PAGE = 3
@router.get("/search_post", response_class=HTMLResponse)
async def search_post(
    request: Request,
    query: str = "",
    page: int = Query(1, alias="page", ge=1),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    query = query.strip()
    try:
        db.execute(text("SELECT 1"))
        # Điều kiện tìm kiếm kết hợp với trạng thái published
        search_filter = func.lower(Article.title).like(func.lower(f"%{query}%")) if query else True
        total_posts = db.query(Article).filter(search_filter, Article.status=="published").count()
        total_pages = math.ceil(total_posts / POSTS_PER_PAGE)
        results = db.query(Article).filter(search_filter, Article.status=="published") \
                     .order_by(Article.date_posted.desc()) \
                     .offset((page - 1) * POSTS_PER_PAGE) \
                     .limit(POSTS_PER_PAGE) \
                     .all()
        base_categories = get_base_categories(db)
        return templates.TemplateResponse(
            "user/search_post.html",
            {
                "request": request,
                "query": query,
                "results": process_images(results),
                "current_page": page,
                "total_pages": total_pages,
                "user": current_user,
                **base_categories,
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi tìm kiếm: {str(e)}")

# Trang video chi tiết
@router.get("/video_detail", response_class=HTMLResponse)
async def video_detail(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    base_categories = get_base_categories(db)
    return templates.TemplateResponse(
        "user/video_detail.html",
        {
            "request": request,
            "user": current_user,
            **base_categories,
        }
    )

# Trang dành cho tác giả
@router.get("/author_page", response_class=HTMLResponse)
async def author_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    base_categories = get_base_categories(db)
    return templates.TemplateResponse(
        "author/Home/index.html",
        {
            "request": request,
            "user": current_user,
            **base_categories,
        }
    )

# Endpoint tải bài viết (chỉ cho Author hoặc Admin)
@router.get("/upload_news", response_class=HTMLResponse)
async def upload_news_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(check_author_or_admin)
):
    base_categories = get_base_categories(db)
    return templates.TemplateResponse(
        "author/Upload_Article/index.html",
        {
            "request": request,
            "user": current_user,
            **base_categories,
        }
    )

@router.post("/api/upload_news")
def upload_news(article: ArticleCreate, db: Session = Depends(get_db)):
    try:
        # Tạo article_id mới tự động
        last_article = db.query(Article.article_id).filter(Article.article_id.like("BB-%")).order_by(Article.article_id.desc()).first()
        last_num = int(last_article.article_id.split('-')[1]) if last_article else 0
        new_id = f"BB-{last_num + 1}"
        # Đảm bảo ID không trùng
        while db.query(Article).filter(Article.article_id == new_id).first():
            last_num += 1
            new_id = f"BB-{last_num + 1}"
        db_article = Article(
            article_id=new_id,
            title=article.title,
            description=article.description,
            content=article.content,
            date_posted=article.date_posted,
            author=article.author,
            source_url=article.source_url,
            status=article.status,
            type=article.type,
            image_urls=article.image_urls,
            video_urls=article.video_urls
        )
        db.add(db_article)
        db.commit()
        db.refresh(db_article)
        return {"message": "Bài viết đã được đăng!", "article_id": new_id}
    except Exception as e:
        print(f"Lỗi trong upload_news: {e}")
        raise HTTPException(status_code=500, detail="Lỗi server, vui lòng thử lại.")

# Trang đăng ký tác giả
@router.get("/signin_author", response_class=HTMLResponse)
async def signin_author(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Bạn cần đăng nhập trước.")
    # Chỉ cho phép người dùng có role "User"
    if current_user.role.lower() != "user":
        raise HTTPException(status_code=403, detail="Chỉ người dùng bình thường mới có thể đăng ký tác giả.")
    base_categories = get_base_categories(db)
    return templates.TemplateResponse(
        "user/signin_author.html",
        {
            "request": request,
            "user": current_user,
            **base_categories,
        }
    )