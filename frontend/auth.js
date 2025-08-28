const API_BASE_URL = "http://127.0.0.1:8000"; 
const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("register-form");
const errorMessage = document.getElementById("error-message");

if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const username = document.getElementById("username").value;
        const password = document.getElementById("password").value;

        // FastAPI's OAuth2PasswordRequestForm expects form data, not JSON
        const formData = new URLSearchParams();
        formData.append("username", username);
        formData.append("password", password);

        try {
            const response = await fetch(`${API_BASE_URL}/token`, {
                method: "POST",
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Login failed");
            }

            const data = await response.json();
            localStorage.setItem("userToken", data.access_token);
            window.location.href = "index.html"; // Redirect to main app
        } catch (error) {
            errorMessage.textContent = error.message;
        }
    });
}

if (registerForm) {
    registerForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const username = document.getElementById("username").value;
        const password = document.getElementById("password").value;

        try {
            const response = await fetch(`${API_BASE_URL}/register`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, password }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Registration failed");
            }

            // Automatically log in after successful registration
            alert("Registration successful! Please log in.");
            window.location.href = "login.html";
        } catch (error) {
            errorMessage.textContent = error.message;
        }
    });
}