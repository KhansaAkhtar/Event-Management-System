function formatErrors(errors) {
    if (typeof errors === 'string') return errors;
    if (Array.isArray(errors)) return errors.join(', ');
    if (typeof errors === 'object') {
        return Object.entries(errors).map(([field, msgs]) => `${field}: ${msgs.join(', ')}`).join(' | ');
    }
    return 'An error occurred';
}
document.addEventListener('DOMContentLoaded', 
function () {
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const errorBox = document.getElementById('errorBox');

            try {
                const response = await fetch('/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });
                const data = await response.json();

                
                if (!response.ok) {
                    errorBox.textContent = data.error || 'Login failed';
                    errorBox.classList.remove('d-none');
                    return;
                }

                localStorage.setItem('token', data.access_token);
                localStorage.setItem('role', data.role);
                localStorage.setItem('name', data.name);
                localStorage.setItem('token', data.access_token);
                localStorage.setItem('role', data.role);
                localStorage.setItem('name', data.name);
                localStorage.setItem('userId', data.id);
                localStorage.setItem('loginTime', Date.now());

                // Role-based redirect
                if (data.role === 'admin' || data.role === 'super_admin') {
                    window.location.href = '/admin-dashboard';
                } else if (data.role === 'vendor') {
                    window.location.href = '/vendor-dashboard';
                } else {
                    window.location.href = '/home';
                }
            } catch (err) {
                errorBox.textContent = 'Something went wrong. Try again.';
                errorBox.classList.remove('d-none');
            }
        });
    }

    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            const name = document.getElementById('name').value;
            const email = document.getElementById('email').value;
            const contact = document.getElementById('contact').value;
            const password = document.getElementById('password').value;
            const role = document.getElementById('role').value;
            const errorBox = document.getElementById('errorBox');

            try {
                const response = await fetch('/auth/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, email, contact, password, role })
                });
                const data = await response.json();

                if (!response.ok) {
                    errorBox.textContent = formatErrors(data.errors || data.error);
                    errorBox.classList.remove('d-none');
                    return;
                }

                showToast('Registered successfully! Please login.', 'success');
                window.location.href = '/login';
            } catch (err) {
                errorBox.textContent = 'Something went wrong. Try again.';
                errorBox.classList.remove('d-none');
            }
        });
    }
});