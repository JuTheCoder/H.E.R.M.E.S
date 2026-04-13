/*
  HERMES Dashboard
  pulls sensor data from the api every 2 seconds
  updates cards, chart, and table
*/

var API_BASE = "";  // same origin, no need to hardcode

var REFRESH_RATE = 2000;

var chartData = {
    labels: [],
    temp: [],
    co2: [],
    aq: [],
    co: [],
    humidity: []
};

var MAX_CHART_POINTS = 30;

var historyChart = null;


// --- api calls (all include credentials for cookie auth) ---

async function fetchSensorData() {
    try {
        var res = await fetch(API_BASE + "/api/data", { credentials: "same-origin" });
        if (res.status === 401) { window.location.href = "/login.html"; return null; }
        if (!res.ok) throw new Error("api unreachable");
        return await res.json();
    } catch (err) {
        console.error("data fetch failed:", err);
        return null;
    }
}

async function fetchThresholds() {
    try {
        var res = await fetch(API_BASE + "/api/threshold", { credentials: "same-origin" });
        if (res.status === 401) return null;
        if (!res.ok) throw new Error("threshold fetch failed");
        return await res.json();
    } catch (err) {
        console.error("threshold fetch failed:", err);
        return null;
    }
}

async function fetchHistory(limit) {
    try {
        var res = await fetch(API_BASE + "/api/history?limit=" + (limit || 20), { credentials: "same-origin" });
        if (res.status === 401) return [];
        if (!res.ok) throw new Error("history fetch failed");
        return await res.json();
    } catch (err) {
        console.error("history fetch failed:", err);
        return [];
    }
}

async function fetchStatus() {
    try {
        var res = await fetch(API_BASE + "/api/status", { credentials: "same-origin" });
        if (res.status === 401) return null;
        if (!res.ok) throw new Error("status check failed");
        return await res.json();
    } catch (err) {
        return null;
    }
}

async function doLogout() {
    await fetch(API_BASE + "/api/logout", { method: "POST", credentials: "same-origin" });
    window.location.href = "/login.html";
}


// --- update the ui ---

function updateCards(data, thresholds) {
    if (!data) return;

    document.getElementById("temp-value").textContent =
        data.temperature ? data.temperature.toFixed(1) : "--";

    document.getElementById("co2-value").textContent =
        data.co2 || "--";

    document.getElementById("co-value").textContent =
        data.co || "--";

    var aqVal = data.aq_percent || data.air || 0;
    document.getElementById("aq-value").textContent = aqVal || "--";

    document.getElementById("humidity-value").textContent =
        data.humidity ? data.humidity.toFixed(1) : "--";

    document.getElementById("robot-location").textContent =
        data.location || "Unknown";

    // alert banner
    var alertBanner = document.getElementById("alert-banner");
    var alertMsg = document.getElementById("alert-message");
    if (data.alert) {
        alertBanner.classList.remove("hidden");
        alertMsg.textContent = "Dangerous conditions detected! Check sensor readings.";
    } else {
        alertBanner.classList.add("hidden");
    }

    if (thresholds) {
        setBadge("temp-status", thresholds.temp_thresh);
        setBadge("co2-status", thresholds.co2_thresh);
        setBadge("co-status", thresholds.co_thresh);
        setBadge("aq-status", thresholds.air_thresh);
        setBadge("humidity-status", thresholds.humidity_thresh || "Unknown");
        setBadge("overall-status", thresholds.overall_thresh || "No Data");
    }

    highlightCard("card-temp", thresholds ? thresholds.temp_thresh : "");
    highlightCard("card-co2", thresholds ? thresholds.co2_thresh : "");
    highlightCard("card-co", thresholds ? thresholds.co_thresh : "");
    highlightCard("card-aq", thresholds ? thresholds.air_thresh : "");
}


function setBadge(elementId, status) {
    var badge = document.getElementById(elementId);
    if (!badge) return;

    badge.textContent = status || "Waiting";
    badge.className = "status-badge";

    var lower = (status || "").toLowerCase();

    if (lower === "safe" || lower === "good" || lower === "comfortable") {
        badge.classList.add("status-safe");
    } else if (lower === "moderate") {
        badge.classList.add("status-moderate");
    } else if (lower === "poor") {
        badge.classList.add("status-poor");
    } else if (lower.includes("unsafe") || lower.includes("unhealthy")) {
        badge.classList.add("status-unsafe");
    } else if (lower.includes("dangerous") || lower.includes("hazardous")) {
        badge.classList.add("status-dangerous");
    } else if (lower.includes("severe")) {
        badge.classList.add("status-severe");
    } else if (lower === "uncomfortable") {
        badge.classList.add("status-uncomfortable");
    } else if (lower === "online") {
        badge.classList.add("status-online");
    } else {
        badge.classList.add("status-waiting");
    }
}


function highlightCard(cardId, status) {
    var card = document.getElementById(cardId);
    if (!card) return;

    var lower = (status || "").toLowerCase();
    var bad = lower.includes("unsafe") || lower.includes("dangerous") ||
              lower.includes("hazardous") || lower.includes("severe") ||
              lower.includes("unhealthy");

    if (bad) {
        card.classList.add("danger");
    } else {
        card.classList.remove("danger");
    }
}


function updateConnectionStatus(isOnline) {
    var dot = document.getElementById("connection-dot");
    var text = document.getElementById("connection-text");

    if (isOnline) {
        dot.className = "dot online";
        text.textContent = "Connected";
    } else {
        dot.className = "dot offline";
        text.textContent = "Disconnected";
    }
}


function updateLastTime() {
    var el = document.getElementById("last-update");
    var now = new Date();
    el.textContent = "Updated: " + now.toLocaleTimeString();
}


// --- history table ---

function updateHistoryTable(history) {
    var tbody = document.getElementById("history-body");
    if (!history || history.length === 0) return;

    var rows = "";
    var recent = history.slice().reverse().slice(0, 20);

    for (var i = 0; i < recent.length; i++) {
        var entry = recent[i];
        var time = entry.timestamp ? entry.timestamp.split(" ")[1] || entry.timestamp : "--";
        var alertClass = entry.alert ? "alert-yes" : "alert-no";
        var alertText = entry.alert ? "YES" : "OK";

        rows += "<tr>";
        rows += "<td>" + time + "</td>";
        rows += "<td>" + (entry.temperature || 0).toFixed(1) + "</td>";
        rows += "<td>" + (entry.co2 || 0) + "</td>";
        rows += "<td>" + (entry.co || 0) + "</td>";
        rows += "<td>" + (entry.aq_percent || entry.air || 0) + "</td>";
        rows += "<td>" + (entry.humidity || 0).toFixed(1) + "</td>";
        rows += "<td>" + (entry.location || "--") + "</td>";
        rows += '<td class="' + alertClass + '">' + alertText + "</td>";
        rows += "</tr>";
    }

    tbody.innerHTML = rows;
}


// --- chart ---

function initChart() {
    var ctx = document.getElementById("history-chart");
    if (!ctx) return;

    historyChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: chartData.labels,
            datasets: [
                {
                    label: "Temp (F)",
                    data: chartData.temp,
                    borderColor: "#e94560",
                    backgroundColor: "rgba(233,69,96,0.1)",
                    borderWidth: 2,
                    tension: 0.3,
                    pointRadius: 2
                },
                {
                    label: "CO2 (ppm)",
                    data: chartData.co2,
                    borderColor: "#f0b429",
                    backgroundColor: "rgba(240,180,41,0.1)",
                    borderWidth: 2,
                    tension: 0.3,
                    pointRadius: 2
                },
                {
                    label: "AQ (%)",
                    data: chartData.aq,
                    borderColor: "#00d97e",
                    backgroundColor: "rgba(0,217,126,0.1)",
                    borderWidth: 2,
                    tension: 0.3,
                    pointRadius: 2
                },
                {
                    label: "Humidity (%)",
                    data: chartData.humidity,
                    borderColor: "#5b8dee",
                    backgroundColor: "rgba(91,141,238,0.1)",
                    borderWidth: 2,
                    tension: 0.3,
                    pointRadius: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: "#8899aa", font: { size: 11 } }
                }
            },
            scales: {
                x: {
                    ticks: { color: "#667788", font: { size: 10 }, maxTicksLimit: 10 },
                    grid: { color: "rgba(255,255,255,0.05)" }
                },
                y: {
                    ticks: { color: "#667788", font: { size: 10 } },
                    grid: { color: "rgba(255,255,255,0.05)" }
                }
            }
        }
    });
}


function addChartPoint(data) {
    if (!historyChart || !data) return;

    var now = new Date();
    var label = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });

    chartData.labels.push(label);
    chartData.temp.push(data.temperature || 0);
    chartData.co2.push(data.co2 || 0);
    chartData.aq.push(data.aq_percent || data.air || 0);
    chartData.humidity.push(data.humidity || 0);

    if (chartData.labels.length > MAX_CHART_POINTS) {
        chartData.labels.shift();
        chartData.temp.shift();
        chartData.co2.shift();
        chartData.aq.shift();
        chartData.humidity.shift();
    }

    historyChart.update();
}


// --- main loop ---

async function refresh() {
    var data = await fetchSensorData();
    var thresholds = await fetchThresholds();
    var status = await fetchStatus();

    var isOnline = (data !== null && status !== null);
    updateConnectionStatus(isOnline);

    if (data) {
        updateCards(data, thresholds);
        addChartPoint(data);
        updateLastTime();
    }

    if (status) {
        document.getElementById("reading-count").textContent =
            status.total_readings || 0;
        setBadge("system-status", status.has_sensor_data ? "Online" : "Waiting");

        // show SMS alert status if the element exists
        var smsEl = document.getElementById("sms-status");
        if (smsEl) {
            smsEl.textContent = status.sms_alerts ? "Active" : "Off";
            smsEl.className = status.sms_alerts ? "sms-active" : "sms-off";
        }
    }

    var history = await fetchHistory(20);
    if (history && history.length > 0) {
        updateHistoryTable(history);
    }

    checkRobotStatus();
}


// robot obstacle handling
async function checkRobotStatus() {
    try {
        var res = await fetch("/api/robot/status", { credentials: "same-origin" });
        if (res.ok) {
            var data = await res.json();
            var blockedEl = document.getElementById("robot-blocked");
            var clearBtn = document.getElementById("clear-btn");
            if (data.blocked) {
                blockedEl.style.display = "inline";
                clearBtn.style.display = "inline";
            } else {
                blockedEl.style.display = "none";
                clearBtn.style.display = "none";
            }
        }
    } catch (err) {}
}

async function clearPath() {
    try {
        await fetch("/api/robot/clear", { method: "POST", credentials: "same-origin" });
        document.getElementById("robot-blocked").style.display = "none";
        document.getElementById("clear-btn").style.display = "none";
    } catch (err) {}
}

// show admin link if logged in as admin
async function checkRole() {
    try {
        var res = await fetch("/api/me", { credentials: "same-origin" });
        if (res.ok) {
            var me = await res.json();
            if (me.role === "admin") {
                var link = document.getElementById("admin-link");
                if (link) link.style.display = "inline";
            }
        }
    } catch (err) {}
}

window.addEventListener("DOMContentLoaded", function () {
    initChart();
    refresh();
    checkRole();
    setInterval(refresh, REFRESH_RATE);
});
