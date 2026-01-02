document.addEventListener("DOMContentLoaded", () => {

    const UPDATE_INTERVAL_MS = 5000;
    let intervalId = null;

    function sendLocation(lat, lon, busId) {
        fetch("/api/update_location", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ bus_id: busId, latitude: lat, longitude: lon })
        })
        .then(res => res.json())
        .then(data => {
            console.log(data);
            if (data.status === "success") {
                document.getElementById("statusMsg").innerText = "Location shared successfully!";
            } else {
                document.getElementById("statusMsg").innerText = "Error in sharing location: " + data.message;
            }
        })
        .catch(err => {
            console.error(err);
            document.getElementById("statusMsg").innerText = "Error in sharing location";
        });
    }

    function updateLocation() {
        const busId = document.getElementById("busId").value;
        if (!busId) {
            document.getElementById("statusMsg").innerText = "Select a bus first!";
            return;
        }

        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                position => {
                    sendLocation(position.coords.latitude, position.coords.longitude, busId);
                },
                error => {
                    console.error("Geolocation error:", error);
                    document.getElementById("statusMsg").innerText = "Error getting location. Allow GPS access!";
                },
                { enableHighAccuracy: true }
            );
        } else {
            document.getElementById("statusMsg").innerText = "Geolocation not supported";
        }
    }

    const startBtn = document.getElementById("startBtn");
    const stopBtn = document.getElementById("stopBtn");

    startBtn.addEventListener("click", () => {
        if (intervalId) clearInterval(intervalId);
        updateLocation(); // send immediately
        intervalId = setInterval(updateLocation, UPDATE_INTERVAL_MS);
        document.getElementById("statusMsg").innerText = "Sharing location every 5 seconds...";
    });

    stopBtn.addEventListener("click", () => {
        if (intervalId) {
            clearInterval(intervalId);
            intervalId = null;
            document.getElementById("statusMsg").innerText = "Location sharing stopped.";
        }
    });
});
