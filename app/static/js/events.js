document.addEventListener('DOMContentLoaded', function () {
    const eventsContainer = document.getElementById('eventsContainer');
    if (eventsContainer) {
        loadEvents();
    }
    const requestForm = document.getElementById('requestEventForm');
    if (requestForm) {
        requestForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            const errorBox = document.getElementById('requestErrorBox');
            const token = localStorage.getItem('token');
            const payload = {
                name: document.getElementById('reqName').value,
                date: document.getElementById('reqDate').value,
                venue: document.getElementById('reqVenue').value,
                capacity: parseInt(document.getElementById('reqCapacity').value),
                description: document.getElementById('reqDescription').value
            };

            try {
                const response = await fetch('/events/request', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
                    body: JSON.stringify(payload)
                });
                const data = await response.json();

                if (!response.ok) {
                    errorBox.textContent = JSON.stringify(data.errors || data.error);
                    errorBox.classList.remove('d-none');
                    return;
                }

                errorBox.classList.add('d-none');
                alert('Request submitted! Admin will review and set a price.');
                requestForm.reset();
            } catch (err) {
                errorBox.textContent = 'Something went wrong.';
                errorBox.classList.remove('d-none');
            }
        });
    }
    async function loadEvents() {
        const token = localStorage.getItem('token');
        if (!token) {
            window.location.href = '/login';
            return;
        }

        try {
            const response = await fetch('/events', {
                headers: { 'Authorization': 'Bearer ' + token }
            });
            const events = await response.json();

            if (!response.ok) {
                eventsContainer.innerHTML = `<p class="text-danger">Failed to load events.</p>`;
                return;
            }

            if (events.length === 0) {
                eventsContainer.innerHTML = `<p>No events available yet.</p>`;
                return;
            }

            eventsContainer.innerHTML = '';
            events.forEach(ev => {
                const card = document.createElement('div');
                card.className = 'col-md-4';
                card.innerHTML = `
                  <div class="card h-100 shadow-sm">
                  <div class="card-body">
                  <h5 class="card-title">${ev.name} <span class="badge bg-secondary">ID: ${ev.id}</span></h5>
                  <p class="card-text mb-1"><strong>Date:</strong> ${ev.date}</p>
                  <p class="card-text mb-1"><strong>Venue:</strong> ${ev.venue}</p>
                  <p class="card-text mb-1"><strong>Capacity:</strong> ${ev.capacity}</p>
                  <span class="badge bg-info text-dark mb-2">${ev.status}</span>
                  <p class="card-text">${ev.description || ''}</p>
                  <button class="btn btn-primary btn-sm bookBtn" data-event-id="${ev.id}"><i class="bi bi-ticket-perforated"></i> Book Event</button>
                  </div>
                  </div>
    `             ;
                eventsContainer.appendChild(card);
            });

            document.querySelectorAll('.bookBtn').forEach(btn => {
                btn.addEventListener('click', async function () {
                    const eventId = this.getAttribute('data-event-id');
                    await bookEvent(eventId);
                });
            });

        } catch (err) {
            eventsContainer.innerHTML = `<p class="text-danger">Something went wrong loading events.</p>`;
        }
    }

    async function bookEvent(eventId) {
        const token = localStorage.getItem('token');
        try {
            const response = await fetch('/bookings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + token
                },
                body: JSON.stringify({ event_id: parseInt(eventId) })
            });
            const data = await response.json();

            if (!response.ok) {
                alert(data.error || 'Booking failed');
                return;
            }
            alert('Event booked successfully!');
        } catch (err) {
            alert('Something went wrong.');
        }
    }
});