document.addEventListener('DOMContentLoaded', function () {
    const myEventsContainer = document.getElementById('myEventsContainer');
    const createForm = document.getElementById('createEventForm');
    const token = localStorage.getItem('token');
    const role = localStorage.getItem('role');

    if (!token) {
        window.location.href = '/login';
        return;
    }

    if (role !== 'admin' && role !== 'super_admin') {
        document.body.innerHTML = `
        <div class="container mt-5">
            <div class="alert alert-danger text-center">
                <h4>Access Denied</h4>
                <p>You don't have permission to view this page. Redirecting...</p>
            </div>
        </div>`;
        setTimeout(() => window.location.href = '/', 2000);
        return;
    }

    if (myEventsContainer) {
        loadMyEvents();
    }

    if (role === 'super_admin') {
    document.getElementById('roleSelector').classList.remove('d-none');

    document.getElementById('showUsersBtn').addEventListener('click', function () {
        document.getElementById('superAdminSection').classList.remove('d-none');
        document.getElementById('manageEventsSection').classList.add('d-none');
        document.getElementById('auditLogSection').classList.add('d-none');
        loadAllUsers();
    });

    document.getElementById('showEventsBtn').addEventListener('click', function () {
        document.getElementById('manageEventsSection').classList.remove('d-none');
        document.getElementById('superAdminSection').classList.add('d-none');
        document.getElementById('auditLogSection').classList.add('d-none');
        loadMyEvents();
        loadPendingEvents();
    });

    document.getElementById('showAuditBtn').addEventListener('click', function () {
        document.getElementById('auditLogSection').classList.remove('d-none');
        document.getElementById('superAdminSection').classList.add('d-none');
        document.getElementById('manageEventsSection').classList.add('d-none');
        loadAuditLog();
    });
} else {
    document.getElementById('manageEventsSection').classList.remove('d-none');
    loadMyEvents();
    loadPendingEvents();
}

    if (createForm) {
        createForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            const errorBox = document.getElementById('createErrorBox');
            const payload = {
                name: document.getElementById('name').value,
                date: document.getElementById('date').value,
                venue: document.getElementById('venue').value,
                capacity: parseInt(document.getElementById('capacity').value),
                price: parseFloat(document.getElementById('price').value),
                description: document.getElementById('description').value
            };

            try {
                const response = await fetch('/events', {
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
                loadMyEvents();
            } catch (err) {
                errorBox.textContent = 'Something went wrong.';
                errorBox.classList.remove('d-none');
            }
        });
    }

    async function loadMyEvents() {
        try {
            const response = await fetch('/events', {
                headers: { 'Authorization': 'Bearer ' + token }
            });
            const events = await response.json();

            if (!response.ok) {
                myEventsContainer.innerHTML = `<p class="text-danger">Failed to load events.</p>`;
                return;
            }

            if (events.length === 0) {
                myEventsContainer.innerHTML = `<p>No events yet. Create one above.</p>`;
                return;
            }

            let html = `<table class="table table-bordered">
                <thead><tr><th>Name</th><th>Date</th><th>Venue</th><th>Capacity</th><th>Status</th><th>Actions</th></tr></thead><tbody>`;

            events.forEach(ev => {
                html += `<tr>
                    <td>${ev.name}</td>
                    <td>${ev.date}</td>
                    <td>${ev.venue}</td>
                    <td>${ev.capacity}</td>
                    <td>${ev.status}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-info viewBookingsBtn" data-id="${ev.id}">Bookings</button>
                        <button class="btn btn-sm btn-outline-secondary viewPaymentsBtn" data-id="${ev.id}">Payments</button>
                        <div class="btn-group">
                            <button class="btn btn-sm btn-outline-dark dropdown-toggle" type="button" data-bs-toggle="dropdown">Reports</button>
                            <ul class="dropdown-menu">
                                <li><a class="dropdown-item reportBtn" href="#" data-id="${ev.id}" data-type="revenue">Revenue (PDF)</a></li>
                                <li><a class="dropdown-item reportBtn" href="#" data-id="${ev.id}" data-type="vendors">Vendors (Excel)</a></li>
                                <li><a class="dropdown-item reportBtn" href="#" data-id="${ev.id}" data-type="payments">Payments (PDF)</a></li>
                            </ul>
                        </div>
                       
                        <button class="btn btn-sm btn-outline-danger deleteBtn" data-id="${ev.id}">Delete</button>
                    </td>
                </tr>`;
            });
            html += `</tbody></table><div id="detailPanel"></div>`;
            myEventsContainer.innerHTML = html;

            document.querySelectorAll('.reportBtn').forEach(btn => {
                btn.addEventListener('click', async function (e) {
                    e.preventDefault();
                    const eventId = this.getAttribute('data-id');
                    const reportType = this.getAttribute('data-type');
                    await downloadReport(eventId, reportType);
                });
            });

            document.querySelectorAll('.deleteBtn').forEach(btn => {
                btn.addEventListener('click', async function () {
                    const confirmed = await showConfirm('Are you sure you want to delete this event?');
                    if (!confirmed) return;
                    const response = await fetch(`/events/${this.getAttribute('data-id')}`, {
                        method: 'DELETE',
                        headers: { 'Authorization': 'Bearer ' + token }
                    });
                    const data = await response.json();

                    if (!response.ok) {
                        showToast(data.error || 'Failed to delete event', 'error');
                        return;
                    }

                    showToast('Event deleted successfully', 'success');
                    loadMyEvents();
                });
            });

            document.querySelectorAll('.viewBookingsBtn').forEach(btn => {
                btn.addEventListener('click', async function () {
                    const eventId = this.getAttribute('data-id');
                    const res = await fetch(`/bookings/event/${eventId}`, {
                        headers: { 'Authorization': 'Bearer ' + token }
                    });
                    const data = await res.json();

                    let html;
                    if (data.length === 0) {
                        html = `<p>No bookings for this event yet.</p>`;
                    } else {
                        html = `<table class="table table-sm table-bordered">
                        <thead><tr><th>Booking ID</th><th>User ID</th><th>Status</th><th>Date</th></tr></thead><tbody>`;
                        data.forEach(b => {
                            html += `<tr><td>${b.id}</td><td>${b.user_id}</td><td>${b.status}</td><td>${new Date(b.booking_date).toLocaleDateString()}</td></tr>`;
                        });
                        html += `</tbody></table>`;
                    }

                    document.getElementById('detailModalLabel').textContent = `Bookings for Event ${eventId}`;
                    document.getElementById('detailModalBody').innerHTML = html;
                    const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('detailModal'));
                    modal.show();
                });
            });

            document.querySelectorAll('.viewPaymentsBtn').forEach(btn => {
                btn.addEventListener('click', async function () {
                    const eventId = this.getAttribute('data-id');
                    const res = await fetch(`/payments/event/${eventId}`, {
                        headers: { 'Authorization': 'Bearer ' + token }
                    });
                    const data = await res.json();

                    let html;
                    if (data.length === 0) {
                        html = `<p>No payments for this event yet.</p>`;
                    } else {
                        html = `<table class="table table-sm table-bordered">
                            <thead><tr><th>Payment ID</th><th>Booking ID</th><th>Amount</th><th>Status</th><th>Action</th></tr></thead><tbody>`;
                        data.forEach(p => {
                            html += `<tr><td>${p.id}</td><td>${p.booking_id}</td><td>${p.amount}</td>
                            <td><span class="badge bg-${p.status === 'paid' ? 'success' : 'warning'}">${p.status}</span></td>
                            <td>${p.status === 'pending' ? `<button class="btn btn-sm btn-outline-success approvePayBtn" data-id="${p.id}">Verify Payment</button>` : '—'}</td></tr>`;
                        });
                        html += `</tbody></table>`;
                    }

                    document.getElementById('detailModalLabel').textContent = `Payments for Event ${eventId}`;
                    document.getElementById('detailModalBody').innerHTML = html;

                    const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('detailModal'));
                    modal.show();

                    document.querySelectorAll('.approvePayBtn').forEach(approveBtn => {
                        approveBtn.addEventListener('click', async function () {
                            const paymentId = this.getAttribute('data-id');
                            await approvePayment(paymentId, eventId);
                        });
                    });
                });
            });

        } catch (err) {
            myEventsContainer.innerHTML = `<p class="text-danger">Something went wrong.</p>`;
        }
    }

    async function loadPendingEvents() {
        const pendingContainer = document.getElementById('pendingEventsContainer');
        if (!pendingContainer) return;

        try {
            const response = await fetch('/events/pending', {
                headers: { 'Authorization': 'Bearer ' + token }
            });
            const events = await response.json();

            if (!response.ok) {
                pendingContainer.innerHTML = `<p class="text-danger">Failed to load pending events.</p>`;
                return;
            }

            if (events.length === 0) {
                pendingContainer.innerHTML = `<p>No pending events.</p>`;
                return;
            }

            let html = `<table class="table table-bordered">
                <thead><tr><th>Name</th><th>Date</th><th>Venue</th><th>Capacity</th><th>Status</th></tr></thead><tbody>`;

            events.forEach(ev => {
                html += `<tr>
                    <td>${ev.name}</td>
                    <td>${ev.date}</td>
                    <td>${ev.venue}</td>
                    <td>${ev.capacity}</td>
                    <td>${ev.status}</td>
                </tr>`;
            });
            html += `</tbody></table>`;
            pendingContainer.innerHTML = html;
        } catch (err) {
            pendingContainer.innerHTML = `<p class="text-danger">Something went wrong.</p>`;
        }
    }

    async function approvePayment(paymentId, eventId) {
        const response = await fetch(`/payments/${paymentId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({ status: 'paid' })
        });
        const data = await response.json();

        if (!response.ok) {
            showToast(data.error || 'Failed to approve payment', 'error');
            return;
        }

        showToast('Payment verified successfully!', 'success');
        document.querySelector(`.viewPaymentsBtn[data-id="${eventId}"]`).click();
    }

    async function downloadReport(eventId, reportType) {
        try {
            const response = await fetch(`/reports/${reportType}/${eventId}`, {
                headers: { 'Authorization': 'Bearer ' + token }
            });

            if (!response.ok) {
                const data = await response.json();
                showToast(data.error || 'Failed to generate report', 'error');
                return;
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;

            const extension = reportType === 'vendors' ? 'xlsx' : 'pdf';
            a.download = `${reportType}_report_event_${eventId}.${extension}`;

            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
        } catch (err) {
            showToast('Something went wrong generating the report.', 'error');
        }
    }

    async function loadAllUsers() {
        const res = await fetch('/users', { headers: { 'Authorization': 'Bearer ' + token } });
        const users = await res.json();

        let html = `<table class="table table-sm table-bordered">
            <thead><tr><th>ID</th><th>Name</th><th>Email</th><th>Role</th><th>Change Role</th><th>Action</th></tr></thead><tbody>`;
        users.forEach(u => {
            html += `<tr>
                <td>${u.id}</td>
                <td>${u.name}</td>
                <td>${u.email}</td>
                <td><span class="badge bg-secondary">${u.role}</span></td>
                <td>
                    <select class="form-select form-select-sm roleSelect" data-id="${u.id}" style="width: auto; display: inline-block;">
                        <option value="user" ${u.role === 'user' ? 'selected' : ''}>User</option>
                        <option value="vendor" ${u.role === 'vendor' ? 'selected' : ''}>Vendor</option>
                    </select>
                    <button class="btn btn-sm btn-outline-primary updateRoleBtn" data-id="${u.id}">Update</button>
                </td>
                <td><button class="btn btn-sm btn-outline-danger deleteUserBtn" data-id="${u.id}">Delete</button></td>
            </tr>`;
        });
        html += `</tbody></table>`;
        document.getElementById('usersContainer').innerHTML = html;

        document.querySelectorAll('.deleteUserBtn').forEach(btn => {
            btn.addEventListener('click', async function () {
                const confirmed = await showConfirm('Are you sure you want to delete this user?');
                if (!confirmed) return;
                await fetch(`/users/${this.getAttribute('data-id')}`, {
                    method: 'DELETE',
                    headers: { 'Authorization': 'Bearer ' + token }
                });
                showToast('User deleted successfully', 'success');
                loadAllUsers();
            });
        });

        document.querySelectorAll('.updateRoleBtn').forEach(btn => {
            btn.addEventListener('click', async function () {
                const userId = this.getAttribute('data-id');
                const select = document.querySelector(`.roleSelect[data-id="${userId}"]`);
                const newRole = select.value;

                const response = await fetch(`/users/${userId}/role`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
                    body: JSON.stringify({ role: newRole })
                });
                const data = await response.json();

                if (!response.ok) {
                    showToast(data.error || 'Failed to update role', 'error');
                    return;
                }
                showToast('Role updated successfully!', 'success');
                loadAllUsers();
            });
        });
    }

    async function loadAuditLog() {
        const res = await fetch('/users/audit-log', { headers: { 'Authorization': 'Bearer ' + token } });
        const logs = await res.json();

        let html = `<table class="table table-sm table-bordered">
            <thead><tr><th>User ID</th><th>Action</th><th>Details</th><th>Time</th></tr></thead><tbody>`;
        logs.forEach(l => {
            html += `<tr><td>${l.user_id || '—'}</td><td><span class="badge bg-secondary">${l.action}</span></td><td>${l.details}</td><td>${new Date(l.timestamp).toLocaleString()}</td></tr>`;
        });
        html += `</tbody></table>`;
        document.getElementById('auditLogContainer').innerHTML = html;
    }
});