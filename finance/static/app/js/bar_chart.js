var endpoint = document.currentScript.getAttribute('api-data')

// get the data data
$.ajax({
	method: "GET",
	url: endpoint,
	success: function(data){
		drawBarChart(data)
	},
	error: function(data){
		console.log("Error in bar_chart.js ajax call.", data)
	}
})

// chart
function drawBarChart(jsonData){
	var data = jsonData;
	var options = {
		scales: {
			xAxes: [{
				stacked: true,
			}],
			yAxes: [{
				stacked: true
			}]
		},
	}
	const ctx = $("#bar_chart");
	var chart = new Chart(ctx, {
		type: 'bar',
		data: data,
		options: options
	});
}