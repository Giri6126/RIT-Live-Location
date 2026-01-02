document.addEventListener("DOMContentLoaded", () => {

    // Initialize map at college coordinates
    const map = L.map('map').setView([13.03849, 80.04536], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19
    }).addTo(map);

    let busMarkers = {};

    function fetchLiveBuses() {
        const routeId = document.getElementById('routeSelect').value;

        fetch(`/api/get_buses_by_route/${routeId}`)
            .then(res => res.json())
            .then(data => {
                if (data.status === "success") {
                    data.buses.forEach(bus => {
                        fetch(`/api/get_location/${bus.bus_id}`)
                            .then(r => r.json())
                            .then(locData => {
                                if (locData.status === "success") {
                                    const lat = locData.location.latitude;
                                    const lon = locData.location.longitude;

                                    if (busMarkers[bus.bus_id]) {
                                        busMarkers[bus.bus_id].setLatLng([lat, lon]);
                                    } else {
                                        busMarkers[bus.bus_id] = L.marker([lat, lon])
                                            .addTo(map)
                                            .bindPopup(`Bus ${bus.bus_id}`);
                                    }
                                }
                            });
                    });
                }
            });
    }

    document.getElementById('routeSelect').addEventListener('change', fetchLiveBuses);

    // Update every 5 seconds
    setInterval(fetchLiveBuses, 5000);
    fetchLiveBuses();
});
