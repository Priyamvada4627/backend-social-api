const form = document.getElementById("registerForm");
const formError = document.getElementById("formError");

form.addEventListener("submit", async (e) => {

    e.preventDefault();

    formError.style.display = "none";
    formError.textContent = "";

    try {

        await apiRequest(
            "/users/",
            "POST",
            {
                username: document.getElementById("username").value,
                full_name: document.getElementById("full_name").value,
                email: document.getElementById("email").value,
                password: document.getElementById("password").value,
            }
        );

        alert("Registration successful!");

        window.location.href = "index.html";

    } catch (err) {

        formError.textContent = err.message;
        formError.style.display = "block";

    }

});