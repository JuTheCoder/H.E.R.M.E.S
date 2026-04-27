
// Testing function to modify each air levels.
function myFunction(){
    document.getElementById("temperature_level").innerHTML = 1.0;
    document.getElementById("co2_level").innerHTML = 10.0;
    document.getElementById("co_level").innerHTML = 5.0;
    document.getElementById("air_level").innerHTML = 20.0;
}

const api_data_url = 'http://127.0.0.1:8000/api/data';
const api_thres_url = 'http://127.0.0.1:8000/api/threshold';
const tempThresholdUrl = "http://127.0.0.1:8000/api/temperature-threshold";
const resetTempThresholdUrl = "http://127.0.0.1:8000/api/reset-temperature-threshold";

// These arrays will hold the data coming from the POST endpoint and will be used to update each graph with the data in it
const labels = [];
const tempData = [];
const co2Data = [];
const coData = [];
const airData = [];

// Creates and displays the temperature data captured by our POST endpoint
const tempChart = new Chart(document.getElementById("tempChart"), {
    type: "line",
    data: {
        labels: labels,
        datasets: [{
            label: "Temperature (F)",
            data: tempData,
            borderWidth: 2,
            tension: 0.3
        }]
    },
    options: {
        responsive: true,
        animation: false
    }
});

// Creates and displays the CO2 data captured by our POST endpoint 
const co2Chart = new Chart(document.getElementById("co2Chart"), {
    type: "line",
    data: {
        labels: labels,
        datasets: [{
            label: "CO2 (PPM)",
            data: co2Data,
            borderWidth: 2,
            tension: 0.3
        }]
    },
    options: {
        responsive: true,
        animation: false
    }
});

// Creates and displays the CO data captured by our POST endpoint 
const coChart = new Chart(document.getElementById("coChart"), {
    type: "line",
    data: {
        labels: labels,
        datasets: [{
            label: "CO (PPM)",
            data: coData,
            borderWidth: 2,
            tension: 0.3
        }]
    },
    options: {
        responsive: true,
        animation: false
    }
});

// Creates and displays the air quality data captured by our POST endpoint 
const airChart = new Chart(document.getElementById("airChart"), {
    type: "line",
    data: {
        labels: labels,
        datasets: [{
            label: "Air Quality (%)",
            data: airData,
            borderWidth: 2,
            tension: 0.3
        }]
    },
    options: {
        responsive: true,
        animation: false
    }
});


// Applies color to each of the thresholds depending on their value
function applyColor(element, value){
    element.className = "badge"

    if (!value){
        element.classList.add("waiting");
        return;
    }

    const v = value.toLowerCase()

    if(v.includes("safe")) element.classList.add("safe");
    else if (v.includes("moderate")) element.classList.add("moderate");
    else if (v.includes("poor")) element.classList.add("poor");
    else if (v.includes("unsafe")) element.classList.add("unsafe");
    else if (v.includes("danger")) element.classList.add("dangerous");
    else element.classList.add("waiting");
}


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
        document.getElementById("air_level").innerHTML = data.air; 

        const now = new Date().toLocaleTimeString();

        labels.push(now);
        tempData.push(data.temperature);
        co2Data.push(data.co2);
        coData.push(data.co);
        airData.push(data.air);

        if (labels.length > 10) {
            labels.shift();
            tempData.shift();
            co2Data.shift();
            coData.shift();
            airData.shift();
        }

        tempChart.update();
        co2Chart.update();
        coChart.update();
        airChart.update();
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

        // Created variables that will hold the threshold values
        const tempEl = document.getElementById("temp_threshold");
        const co2El = document.getElementById("co2_threshold");
        const coEl = document.getElementById("co_threshold");
        const airEl = document.getElementById("air_threshold");
        const overallEl = document.getElementById("overall_threshold");

        // Display the thresholds
        tempEl.innerHTML = data.temp_thresh;
        co2El.innerHTML = data.co2_thresh;
        coEl.innerHTML = data.co_thresh;
        airEl.innerHTML = data.air_thresh;
        overallEl.innerHTML = data.overall_thresh;

        // This will apply colors using the applyColor function above
        applyColor(tempEl, data.temp_thresh);
        applyColor(co2El, data.co2_thresh);
        applyColor(coEl, data.co_thresh);
        applyColor(airEl, data.air_thresh);
        applyColor(overallEl, data.overall_thresh);

    } catch (error) {
        console.error("Error fetching thresholds:", error);
    }
}

async function saveTemperatureThresholds(){

    // Checking if any of the input boxes are empty
    if(
        document.getElementById("safe_min").value === "" ||
        document.getElementById("safe_max").value === "" ||
        document.getElementById("moderate_low_min").value === "" ||
        document.getElementById("moderate_low_max").value === "" ||
        document.getElementById("moderate_high_min").value === "" ||
        document.getElementById("moderate_high_max").value === ""
    ) {
        alert("Please fill in all threshold fields");
        return;
    }

    // Grabs the values from the frontend boxes, converts them into numbers, and then stores them in their corresponding object/variable
    const payload = {
        safe_min: Number(document.getElementById("safe_min").value),
        safe_max: Number(document.getElementById("safe_max").value),
        moderate_low_min: Number(document.getElementById("moderate_low_min").value),
        moderate_low_max: Number(document.getElementById("moderate_low_max").value),
        moderate_high_min: Number(document.getElementById("moderate_high_min").value),
        moderate_high_max: Number(document.getElementById("moderate_high_max").value)
    };

    // Sends the new data from the user to the backend using the POST endpoint
    try{
        const res = await fetch(tempThresholdUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        if(!res.ok) throw new Error("Failed to save temperature thresholds");

        const data = await res.json();
        console.log("Saved temperature thresholds:", data);
        alert("Temperature thresholds updated successfully");
        fetchThresholds();                                                      // Refreshing the thresholds
    } catch(error){
        console.error("Errpr saving temperature thresholds:", error);
        alert("Could not save thresholds");
    }
}

async function resetTemperatureThresholds() {
    try{
        const res = await fetch(resetTempThresholdUrl, {
            method: "POST"
        });

        if(!res.ok) throw new Error("Failed to reset temperature thresholds");

        const data = await res.json();
        console.log("Reset temperature thresholds:", data);
        alert("Temperature thresholds reset to default");
        fetchThresholds();
    } catch(error){
        console.error("Error resetting temperature thresholds:", error);
        alert("Could not reset thresholds");
    }
}

// Refresh every 2 seconds
setInterval(fetchData, 2000);
setInterval(fetchThresholds, 2000);

// Run once immediately
fetchData();
fetchThresholds();
