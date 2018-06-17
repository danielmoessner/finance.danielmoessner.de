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
	}
})

// chart
function drawLineChart(jsonData){
	var data = jsonData;
	var options = {
		tooltips: {
            enabled: true,
            mode: 'single',
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
			yAxes: [
				{
	                type: "linear",
	                position: "left",
	                id: "yield",
	                ticks: {
				        callback: function(value) {
				            return value + "%"
			            }
				    },
				    scaleLabel: {
			           	display: true,
			           	labelString: "Percentage"
			       	}
            	}, 
            	{
	                type: "linear",
	                position: "right",
	                id: "value",
	                scaleLabel: {
			           	display: true,
			           	labelString: "Value"
			       	}
	            }
            ],
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
