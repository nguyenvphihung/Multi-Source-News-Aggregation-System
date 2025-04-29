document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("loginForm").addEventListener("submit", async function(event) {
        event.preventDefault();
    
        let formData = new URLSearchParams(new FormData(this));
    
        let response = await fetch("/login", {
            method: "POST",
            body: formData,
            headers: { 
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded"
            }
        });
    
        try {
            let result = await response.json();
            if (response.ok) {
                alert(result.message);
                window.location.href = "/home";  
            } else {
                alert(result.detail);
            }
        } catch (error) {
            console.error("Lỗi parse JSON:", error);
            alert("Lỗi hệ thống!");
        }
    });
});
