document.addEventListener('DOMContentLoaded', function () {
    const token = localStorage.getItem('token');
    const role = localStorage.getItem('role');

    if (role !== 'vendor') {
        showToast('Access denied: Vendors only');
        window.location.href = '/';
        return;
    }

    const myVendorContainer = document.getElementById('myVendorContainer');
    const createForm = document.getElementById('createVendorForm');

    if (myVendorContainer) {
        loadMyServices();
    }

    if (createForm) {
        createForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            const errorBox = document.getElementById('createErrorBox');
            const payload = {
                service_type: document.getElementById('serviceType').value,
                event_id: parseInt(document.getElementById('eventId').value)
            };

            try {
                const response = await fetch('/vendors', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + token
                    },
                    body: JSON.stringify(payload)
                });
                const data = await response.json();

                if (!response.ok) {
                    errorBox.textContent = JSON.stringify(data.errors || data.error);
                    errorBox.classList.remove('d-none');
                    return;
                }

                errorBox.classList.add('d-none');
                createForm.reset();
                loadMyServices();
            } catch (err) {
                errorBox.textContent = 'Something went wrong.';
                errorBox.classList.remove('d-none');
            }
        });
    }

    async function loadMyServices() {
        try {
            const response = await fetch('/vendors/my', {
                headers: { 'Authorization': 'Bearer ' + token }
            });
            const services = await response.json();

            if (!response.ok) {
                myVendorContainer.innerHTML = `<p class="text-danger">Failed to load services.</p>`;
                return;
            }

            if (services.length === 0) {
                myVendorContainer.innerHTML = `<p>No services added yet.</p>`;
                return;
            }

            let html = `<table class="table table-bordered">
                <thead><tr><th>ID</th><th>Service Type</th><th>Event ID</th><th>Action</th></tr></thead><tbody>`;

            services.forEach(v => {
                html += `<tr>
                    <td>${v.id}</td>
                    <td>${v.service_type}</td>
                    <td>${v.event_id}</td>
                    <td><button class="btn btn-sm btn-outline-danger deleteBtn" data-id="${v.id}">Delete</button></td>
                </tr>`;
            });
            html += `</tbody></table>`;
            myVendorContainer.innerHTML = html;

            document.querySelectorAll('.deleteBtn').forEach(btn => {
                btn.addEventListener('click', async function () {
                    if (!confirm('Delete this service?')) return;
                    await fetch(`/vendors/${this.getAttribute('data-id')}`, {
                        method: 'DELETE',
                        headers: { 'Authorization': 'Bearer ' + token }
                    });
                    loadMyServices();
                });
            });

        } catch (err) {
            myVendorContainer.innerHTML = `<p class="text-danger">Something went wrong.</p>`;
        }
    }
});