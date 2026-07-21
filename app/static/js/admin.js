document.addEventListener('DOMContentLoaded', function () {
    const myEventsContainer = document.getElementById('myEventsContainer');
    const createForm = document.getElementById('createEventForm');
    const token = localStorage.getItem('token');
    const role = localStorage.getItem('role'); 
    if (role !== 'admin' && role !== 'super_admin') {
    document.body.innerHTML = `
    <div class="container mt-5">
        <div class="alert alert-danger text-center">
            <h4>Access Denied</h4>
            <p>You don't have permission to view this page. Redirecting...</p>
        </div>
    </div>`;
setTimeout(() => window.location.href = '/', 2000);
    }

    if (myEventsContainer) {
        loadMyEvents();
    }
    if (!token) {
        window.location.href = '/login';
        return;
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
                            <button class="btn btn-sm btn-outline-dark dropdown-toggle" data-bs-toggle="dropdown">Reports</button>
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
                    if (!confirm('Delete this event?')) return;
                    await fetch(`/events/${this.getAttribute('data-id')}`, {
                        method: 'DELETE',
                        headers: { 'Authorization': 'Bearer ' + token }
                    });
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
                    if (data.length === 0) {
                    document.getElementById('detailPanel').innerHTML =  `<p class="mt-3">No bookings for this event yet.</p>`;
                      return;
                      }

                    let html = `<h6 class="mt-3">Bookings for Event ${eventId}</h6>
                    <table class="table table-sm table-bordered">
                    <thead><tr><th>Booking ID</th><th>User ID</th><th>Status</th><th>Date</th></tr></thead><tbody>`;
                    data.forEach(b => {
                    html += `<tr><td>${b.id}</td><td>${b.user_id}</td><td>${b.status}</td><td>${new Date(b.booking_date).toLocaleDateString()}</td></tr>`;
                    });
                    html += `</tbody></table>`;
                    document.getElementById('detailPanel').innerHTML = html;
                });
            });

            document.querySelectorAll('.viewPaymentsBtn').forEach(btn => {
            btn.addEventListener('click', async function () {
            const eventId = this.getAttribute('data-id');
            const res = await fetch(`/payments/event/${eventId}`, {
            headers: { 'Authorization': 'Bearer ' + token }
            });
            const data = await res.json();

            if (data.length === 0) {
            document.getElementById('detailPanel').innerHTML = `<p class="mt-3">No payments for this event yet.</p>`;
            return;
            }

            let html = `<h6 class="mt-3">Payments for Event ${eventId}</h6>
            <table class="table table-sm table-bordered">
                <thead><tr><th>Payment ID</th><th>Booking ID</th><th>Amount</th><th>Status</th></tr></thead><tbody>`;
            data.forEach(p => {
            html += `<tr><td>${p.id}</td><td>${p.booking_id}</td><td>${p.amount}</td><td><span class="badge bg-${p.status === 'paid' ? 'success' : 'warning'}">${p.status}</span></td></tr>`;
            });
            html += `</tbody></table>`;
            document.getElementById('detailPanel').innerHTML = html;
            // inside viewPaymentsBtn handler in admin.js, add a button per row:
            html += `<tr><td>${p.id}</td><td>${p.booking_id}</td><td>${p.amount}</td>
            <td><span class="badge bg-${p.status === 'paid' ? 'success' : 'warning'}">${p.status}</span></td>
            <td>${p.status === 'pending' ? `<button class="btn btn-sm btn-outline-success approvePayBtn" data-id="${p.id}">Approve</button>` : ''}</td></tr>`;
        });
    });

        } catch (err) {
            myEventsContainer.innerHTML = `<p class="text-danger">Something went wrong.</p>`;
        }
    }
});
async function downloadReport(eventId, reportType) {
    const token = localStorage.getItem('token'); 
    try {
        const response = await fetch(`/reports/${reportType}/${eventId}`, {
            headers: { 'Authorization': 'Bearer ' + token }
        });

        if (!response.ok) {
            const data = await response.json();
            alert(data.error || 'Failed to generate report');
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
        alert('Something went wrong generating the report.');
    }
}