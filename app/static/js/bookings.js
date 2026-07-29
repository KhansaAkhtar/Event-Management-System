document.addEventListener('DOMContentLoaded', function () {
    const bookingsContainer = document.getElementById('bookingsContainer');
    const token = localStorage.getItem('token');

    if (bookingsContainer) {
        loadMyBookings();
    }

    async function loadMyBookings() {
        if (!token) {
            window.location.href = '/login';
            return;
        }

        try {
            const response = await fetch('/bookings/my', {
                headers: { 'Authorization': 'Bearer ' + token }
            });
            const bookings = await response.json();

            if (!response.ok) {
                bookingsContainer.innerHTML = `<p class="text-danger">Failed to load bookings.</p>`;
                return;
            }

            if (bookings.length === 0) {
                bookingsContainer.innerHTML = `<p>You have no bookings yet.</p>`;
                return;
            }

            let html = `<table class="table table-bordered align-middle">
                <thead><tr><th>Booking ID</th><th>Event</th><th>Price</th><th>Booking Status</th><th>Payment Status</th><th>Date</th><th>Actions</th></tr></thead><tbody>`;

            bookings.forEach(b => {
                let paymentBadge;
                if (b.status === 'cancelled') {
                    paymentBadge = `<span class="badge bg-secondary">N/A</span>`;
                } else if (b.payment_status === 'paid') {
                    paymentBadge = `<span class="badge bg-success">Paid</span>`;
                } else if (b.payment_status === 'pending') {
                    paymentBadge = `<span class="badge bg-warning">Pending Verification</span>`;
                } else {
                    paymentBadge = `<span class="badge bg-secondary">Not Paid</span>`;
                }

                let actions = '';
                if (b.status !== 'cancelled') {
                    if (b.payment_status !== 'paid' && b.payment_status !== 'pending') {
                        actions += `<button class="btn btn-sm btn-outline-primary payBtn me-1" data-booking-id="${b.id}" data-amount="${b.event_price}">Pay</button>`;
                    }
                    actions += `<button class="btn btn-sm btn-outline-danger cancelBtn" data-booking-id="${b.id}">Cancel</button>`;
                } else {
                    actions = '—';
                }

                html += `<tr>
                    <td>${b.id}</td>
                    <td>${b.event_name} (ID: ${b.event_id})</td>
                    <td>Rs. ${b.event_price}</td>
                    <td><span class="badge bg-${b.status === 'cancelled' ? 'danger' : 'success'}">${b.status}</span></td>
                    <td>${paymentBadge}</td>
                    <td>${new Date(b.booking_date).toLocaleDateString()}</td>
                    <td>${actions}</td>
                </tr>`;
            });
            html += `</tbody></table>`;
            bookingsContainer.innerHTML = html;

            document.querySelectorAll('.cancelBtn').forEach(btn => {
                btn.addEventListener('click', async function () {
                    await cancelBooking(this.getAttribute('data-booking-id'));
                });
            });

            document.querySelectorAll('.payBtn').forEach(btn => {
                btn.addEventListener('click', async function () {
                    const bookingId = this.getAttribute('data-booking-id');
                    const amount = this.getAttribute('data-amount');
                    await payForBooking(bookingId, amount);
                });
            });

        } catch (err) {
            bookingsContainer.innerHTML = `<p class="text-danger">Something went wrong.</p>`;
        }
    }

    async function cancelBooking(bookingId) {
        const response = await fetch(`/bookings/${bookingId}/cancel`, {
            method: 'PUT',
            headers: { 'Authorization': 'Bearer ' + token }
        });
        const data = await response.json();
        if (!response.ok) {
            showToast(data.error || 'Cancel Failed!', 'error')
            return;
        }
        showToast('Booking cancelled', 'success');
        loadMyBookings();
    }

    async function payForBooking(bookingId, amount) {
        const response = await fetch('/payments', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({ booking_id: parseInt(bookingId), amount: parseFloat(amount) })
        });
        const data = await response.json();
        if (!response.ok) {
            showToast(data.error || 'Payment failed', 'error');
            return;
        }
        showToast('Payment submitted (pending approval)', 'success');
        loadMyBookings();
    }
});