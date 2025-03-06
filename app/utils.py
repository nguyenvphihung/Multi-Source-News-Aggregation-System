def get_first_image(image_urls: str) -> str:
    """
    Lấy ảnh đầu tiên từ chuỗi `image_urls`. Nếu không có, trả về ảnh mặc định.
    """
    if image_urls:
        return image_urls.split(",")[0].strip()  # Lấy ảnh đầu tiên
    return "/static/images/default-thumbnail.jpg"  # Ảnh mặc định


def process_images(posts):
    """Xử lý danh sách bài viết để lấy ảnh đầu tiên."""
    for post in posts:
        post.image_urls = get_first_image(post.image_urls) if post.image_urls else ""
    return posts
