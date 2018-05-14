var endpoint = document.currentScript.getAttribute('api-data')

// get the lineChartData
$.ajax({
	method: "GET",
	url: endpoint,
	success: function(data){
		drawLineChart(data)
	},
	error: function(xhr, ajaxOptions, thrownError){
		console.log("Error in line_chart.js ajax call.")
		console.log(xhr.status)
		console.log(thrownError)
	}
})

// chart
function drawLineChart(jsonData){
	var data = jsonData;
	var options = {
		tooltips: {
            enabled: true,
            mode: 'single',
             callbacks: {
                label: function(tooltipItems, data) {
                    return data.datasets[tooltipItems.datasetIndex].label +': ' + tooltipItems.yLabel + ' €';
                }
            }
        },
		scales: {
			xAxes: [{
				type: 'time',
				display: true,
				time: {
					displayFormats: {
						'millisecond': 'DD MMM',
						'second': 'DD MMM',
						'minute': 'DD MMM',
						'hour': 'DD MMM',
						'day': 'DD MMM',
						'week': 'DD MMM',
						'month': 'DD MMM',
						'quarter': 'DD MMM',
						'year': 'DDs MMM YYYY',
					}
				}
			}],
		},
		elements: {
	        line: {
	            tension: 0
	        }
	    }
	}
	const ctx = $("#line_chart");
	var chart = new Chart(ctx, {
		type: 'line',
		data: data,
		options: options
	});
	updateChartColors(chart);
}
