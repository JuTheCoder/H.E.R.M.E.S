
// Testing function to modify each air levels.
function myFunction(){
    document.getElementById("temperature_level").innerHTML = 1.0;
    document.getElementById("co2_level").innerHTML = 10.0;
    document.getElementById("co_level").innerHTML = 5.0;
    document.getElementById("air_level").innerHTML = 20.0;
}

const api_data_url = 'http://127.0.0.1:8000/api/data';
const api_thres_url = 'http://127.0.0.1:8000/api/threshold';

// Fetch sensor values
async function fetchData() {
    try {
        const res = await fetch(api_data_url);
        if (!res.ok) throw new Error("Data fetch failed");

        const data = await res.json();

        console.log("Sensor:", data);

        document.getElementById("temperature_level").innerHTML = data.temperature;
        document.getElementById("co2_level").innerHTML = data.co2;
        document.getElementById("co_level").innerHTML = data.co;
        document.getElementById("air_level").innerHTML = data.air; // important change

    } catch (error) {
        console.error("Error fetching data:", error);
    }
}

// Fetch thresholds
async function fetchThresholds() {
    try {
        const res = await fetch(api_thres_url);
        if (!res.ok) throw new Error("Threshold fetch failed");

        const data = await res.json();

        console.log("Thresholds:", data);

        document.getElementById("temp_threshold").innerHTML = data.temp_thresh;
        document.getElementById("co2_threshold").innerHTML = data.co2_thresh;
        document.getElementById("co_threshold").innerHTML = data.co_thresh;
        document.getElementById("air_threshold").innerHTML = data.air_thresh;

    } catch (error) {
        console.error("Error fetching thresholds:", error);
    }
}

// Refresh every 2 seconds
setInterval(fetchData, 2000);
setInterval(fetchThresholds, 2000);

// Run once immediately
fetchData();
fetchThresholds();
