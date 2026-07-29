let weatherRefreshInterval = null;

document.addEventListener('DOMContentLoaded', function () {
    const eventsContainer = document.getElementById('eventsContainer');
    if (eventsContainer) {
        loadEvents();
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
                const isFull = ev.status === 'full';
                card.className = 'col-md-4';
                card.innerHTML = `
                  <div class="card h-100 shadow-sm">
                  <div class="card-body">
                  <h5 class="card-title">${ev.name} <span class="badge bg-secondary">ID: ${ev.id}</span></h5>
                  <p class="card-text mb-1"><strong>Date:</strong> ${ev.date}</p>
                  <p class="card-text mb-1"><strong>Venue:</strong> ${ev.venue}</p>
                  <p class="card-text mb-1"><strong>Capacity:</strong> ${ev.capacity}</p>
                  <span class="badge bg-${isFull ? 'danger' : 'info'} text-dark mb-2">${ev.status}</span>
                  <p class="card-text">${ev.description || ''}</p>
                  <button class="btn btn-outline-secondary btn-sm mapBtn" data-venue="${ev.venue}" data-name="${ev.name}">
                  <i class="bi bi-geo-alt"></i> View Map
                  </button>
                  <button class="btn btn-outline-info btn-sm weatherBtn" data-id="${ev.id}">
                  <i class="bi bi-cloud-sun"></i> Weather
                  </button>
                  <button class="btn ${isFull ? 'btn-warning' : 'btn-primary'} btn-sm bookBtn" data-event-id="${ev.id}">
                  <i class="bi bi-ticket-perforated"></i> ${isFull ? 'Join Waitlist' : 'Book Event'}
                  </button>
                  </div>
                  </div>
                `;
                eventsContainer.appendChild(card);
            });

            document.querySelectorAll('.bookBtn').forEach(btn => {
                btn.addEventListener('click', async function () {
                    const eventId = this.getAttribute('data-event-id');
                    await bookEvent(eventId);
                });
            });

            document.querySelectorAll('.mapBtn').forEach(btn => {
                btn.addEventListener('click', function () {
                    const venue = this.getAttribute('data-venue');
                    const name = this.getAttribute('data-name');
                    const encodedVenue = encodeURIComponent(venue);

                    document.getElementById('mapModalLabel').textContent = name;
                    document.getElementById('mapFrame').src = `https://maps.google.com/maps?q=${encodedVenue}&z=15&output=embed`;
                    document.getElementById('directionsLink').href = `https://www.google.com/maps/dir/?api=1&destination=${encodedVenue}`;

                    const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('mapModal'));
                    modal.show();
                });
            });

            // YE HISSA AB SAHI JAGAH PE HAI — cards banne ke turant baad
            document.querySelectorAll('.weatherBtn').forEach(btn => {
                btn.addEventListener('click', function () {
                    const eventId = this.getAttribute('data-id');
                    loadWeather(eventId);

                    const modalEl = document.getElementById('weatherModal');
                    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
                    modal.show();

                    if (weatherRefreshInterval) clearInterval(weatherRefreshInterval);
                    weatherRefreshInterval = setInterval(() => loadWeather(eventId), 10 * 60 * 1000);

                    modalEl.addEventListener('hidden.bs.modal', function stopRefresh() {
                        clearInterval(weatherRefreshInterval);
                        modalEl.removeEventListener('hidden.bs.modal', stopRefresh);
                    }, { once: true });
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
                headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
                body: JSON.stringify({ event_id: parseInt(eventId) })
            });
            const data = await response.json();

            if (!response.ok) {
                showToast(data.error || 'Booking failed', 'error');
                return;
            }
            showToast(data.message || 'Success!', 'success');
            loadEvents();
        } catch (err) {
            showToast('Something went wrong.', 'error');
        }
    }

    async function loadWeather(eventId) {
        const token = localStorage.getItem('token');
        const body = document.getElementById('weatherModalBody');
        body.innerHTML = 'Loading...';

        try {
            const response = await fetch(`/events/${eventId}/weather`, {
                headers: { 'Authorization': 'Bearer ' + token }
            });
            const data = await response.json();

            if (!response.ok) {
                body.innerHTML = `<p class="text-danger">${data.error || 'Failed to load weather.'}</p>`;
                return;
            }

            let html = `<p><strong>Venue:</strong> ${data.venue}</p>`;

            if (data.severe_warning) {
                html += `<div class="alert alert-danger"><i class="bi bi-exclamation-triangle"></i> Severe weather expected — plan accordingly!</div>`;
            }

            html += `
                <p><strong>Current:</strong> ${data.current_temp}°C, ${data.condition}</p>
                <p><strong>Wind Speed:</strong> ${data.wind_speed} km/h</p>
                <p><strong>Today's Forecast:</strong> ${data.forecast_min_temp}°C – ${data.forecast_max_temp}°C</p>
            `;

            document.getElementById('weatherModalLabel').textContent = `Weather — ${data.venue}`;
            body.innerHTML = html;
        } catch (err) {
            body.innerHTML = `<p class="text-danger">Something went wrong.</p>`;
        }
    }
});