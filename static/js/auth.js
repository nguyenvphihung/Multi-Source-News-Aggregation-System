import { auth, onAuthStateChanged, signOut } from "./firebase-config.js";
import {
    signInWithEmailAndPassword,
    signInWithPopup,
    GoogleAuthProvider,
    createUserWithEmailAndPassword,
    sendEmailVerification
} from "https://www.gstatic.com/firebasejs/11.1.0/firebase-auth.js";

// Xử lý đăng nhập bằng Google
const googleLoginButton = document.querySelector('.social-btn.google');
if (googleLoginButton) {
    googleLoginButton.addEventListener('click', async () => {
        const provider = new GoogleAuthProvider();

        try {
            const result = await signInWithPopup(auth, provider);

            const user = result.user;


            
            alert(`Đăng nhập Google thành công! Xin chào ${result.user.displayName}`);

            window.location.href = '/home';
        } catch (error) {
            alert(`Đăng nhập Google thất bại: ${error.message}`);
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    console.log("Kiểm tra Firebase Auth:", auth);

    onAuthStateChanged(auth, (user) => {
        console.log("Trạng thái đăng nhập:", user);

        if (user) {
            document.getElementById("user-profile").classList.remove("d-none");
            document.getElementById("signup-btn").style.display = "none";
            document.getElementById("user-avatar").src = user.photoURL || "/static/default-avatar.png";
            document.getElementById("user-name").textContent = user.displayName || "Người dùng";
        } else {
            document.getElementById("user-profile").classList.add("d-none");
            document.getElementById("signup-btn").style.display = "block";
        }
    });

    let userProfile = document.getElementById("user-profile");
    let menuContent = document.getElementById("menu-content");

    if (userProfile && menuContent) {
        // Khi rê chuột vào avatar hoặc menu
        userProfile.addEventListener("mouseenter", () => {
            menuContent.classList.add("show");
        });

        // Khi rời chuột khỏi avatar hoặc menu
        userProfile.addEventListener("mouseleave", () => {
            menuContent.classList.remove("show");
        });
    } else {
        console.error("Lỗi: Không tìm thấy user-profile hoặc menu-content.");
    }
});

// Xử lý đăng xuất
document.getElementById("logout-btn")?.addEventListener("click", () => {
  signOut(auth)
      .then(() => {
          alert("Bạn đã đăng xuất!");
          window.location.reload(); // Tải lại trang
      })
      .catch((error) => {
          console.error("Lỗi đăng xuất:", error);
      });
});