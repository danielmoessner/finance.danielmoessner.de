var endpoint = document.currentScript.getAttribute('api-data')

// get the data data
$.ajax({
	method: "GET",
	url: endpoint,
	success: function(data){
		drawStackedBarChart(data)
	},
	error: function(data){
		console.log("Error in stacked_bar_chart.js ajax call.", data)
	}
})

// chart
function drawStackedBarChart(jsonData){
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
	const ctx = $("#stacked_bar_chart");
	var chart = new Chart(ctx, {
		type: 'bar',
		data: data,
		options: options
	});
	updateChartColors(chart);
}