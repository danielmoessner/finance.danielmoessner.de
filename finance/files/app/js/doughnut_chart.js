var endpoint = document.currentScript.getAttribute('api-data')

// get the data data has to look like pie cake chart data
$.ajax({
	method: "GET",
	url: endpoint,
	success: function(data){
		drawDoughnutChart(data)
	},
	error: function(data){
		console.log("Error in doughnut_chart.js ajax call.", data)
	}
})

// chart
function drawDoughnutChart(jsonData){
	var data = jsonData;
	var options = {
		elements: {
			arc: {
				borderWidth: 0
			}
		},
		tooltips: {
			callbacks: {
				label: function(tooltipItem, data) {
					var dataset = data.datasets[tooltipItem.datasetIndex];
					var currentValue = dataset.data[tooltipItem.index];
					return currentValue + "%";
				}
			}
		} ,
		responsive: false,
		maintainAspectRatio: true,
	}
	const ctx = $("#doughnut_chart");
	var chart = new Chart(ctx, {
		type: 'doughnut',
		data: data,
		options: options
	});
	updateChartColors(chart)
}