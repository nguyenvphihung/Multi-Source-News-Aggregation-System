document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("registerForm").addEventListener("submit", async function(event) {
        event.preventDefault();

        let formData = new FormData(this);

        // Debug: In dữ liệu trước khi gửi
        for (let [key, value] of formData.entries()) {
            console.log(`${key}: ${value}`);
        }

        let response = await fetch("/register", {
            method: "POST",
            body: formData,
            headers: { "Accept": "application/json" }  // Không đặt "Content-Type", FormData sẽ tự động xử lý
        });

        let result = await response.json();
        if (response.ok) {
            alert(result.message);
            window.location.href = "/login";
        } else {
            alert(result.detail);
        }
    });
});
