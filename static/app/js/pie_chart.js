var endpoint = document.currentScript.getAttribute("api-data")

// get the data
$.ajax({
	method: "GET",
	url: endpoint,
	success: function(data){
		drawPieChart(data)
	},
	error: function(data){
		console.log("Error in cake_chart.js ajax call.", data)
	}
})

// chart
function drawPieChart(jsonData){
    var data = jsonData
    var options = {
		elements: {
			arc: {
				borderWidth: 0
			}
		},
		legend: {
			reverse: true
		}
	}
	const ctx = $("#pie_chart");
	var chart = new Chart(ctx, {
		type: "pie",
		data: data,
		options: options
	});
	updateChartColors(chart)
}