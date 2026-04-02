
// Testing function to modify each air levels.
function myFunction(){
    document.getElementById("temperature_level").innerHTML = 1.0;
    document.getElementById("co2_level").innerHTML = 10.0;
    document.getElementById("co_level").innerHTML = 5.0;
    document.getElementById("air_level").innerHTML = 20.0;
}

const api_data_url = 'http://127.0.0.1:8000/api/data';
const api_thres_url = 'http://127.0.0.1:8000/api/threshold';

// Fetching the data endpoint
fetch(api_data_url)
    .then(response =>{
        if (!response.ok){
            throw new Error('Network response was not ok');
        }
        return response.json(); // Parse the JSON response
    })
    .then(data => {
        console.log(data); // Handle the response data
        // Ex: display data in an HTML element
       // document.getElementById("test").innerHTML = data.message;
        document.getElementById("temperature_level").innerHTML = data.temperature;
        document.getElementById("co2_level").innerHTML = data.co2;
        document.getElementById("co_level").innerHTML = data.co;
        document.getElementById("air_level").innerHTML = data.air_quality;
    })
    .catch(error => {
        console.error('Problem with fetch operation: ', error);
    });

// fetching the threshold endpoint
fetch(api_thres_url)
    .then(response =>{
        if (!response.ok){
            throw new Error('Network response was not ok');
        }
        return response.json()
    })
    .then(data => {
        console.log(data);

        document.getElementById("temp_threshold").innerHTML = data.temp_thresh;
        document.getElementById("co2_threshold").innerHTML = data.co2_thresh;
        document.getElementById("co_threshold").innerHTML = data.co_thresh;
        document.getElementById("air_threshold").innerHTML = data.air_thresh;
    })


