function toggleMenu() {
    let menu = document.querySelector(".nav-topbar");
    if (menu) {
        menu.classList.toggle("show");
    } else {
        console.error("Lỗi: Không tìm thấy nav-topbar.");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    let hamburgerMenu = document.querySelector(".hamburger-menu");
    let navTopbar = document.querySelector(".nav-topbar");
    let mainNav = document.querySelector(".main-nav");
    let topBar = document.querySelector(".top-bar");

    function moveNavTopbar() {
        if (!navTopbar || !mainNav || !topBar) {
            console.error("Lỗi: Không tìm thấy một trong các phần tử cần thiết");
            return;
        }

        if (window.innerWidth <= 768) {
            if (!mainNav.contains(navTopbar)) {
                mainNav.appendChild(navTopbar);
            }
        } else {
            if (!topBar.contains(navTopbar)) {
                topBar.appendChild(navTopbar);
            }
        }
    }

    moveNavTopbar();
    window.addEventListener("resize", moveNavTopbar);

    if (hamburgerMenu) {
        hamburgerMenu.addEventListener("click", toggleMenu);
    }
});