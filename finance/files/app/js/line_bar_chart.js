var endpoint = document.currentScript.getAttribute('api-data')

// get the data
$.ajax({
	method: "GET",
	url: endpoint,
	success: function(data){
		drawLineBarChart(data)
	},
	error: function(data){
		console.log("Error in line_bar_chart.js ajax call.", data)
	}
})

// chart
function drawLineBarChart(jsonData){
	var data = jsonData
	var options = {
		elements: {
	        line: {
	            tension: 0
	        }
	    },
		tooltips: {
            enabled: true,
            mode: 'single',
            callbacks: {
            	title: function(tooltipItem, data) {
                    var title = data.labels[tooltipItem[0].index] || '';
                    title = title.substring(0,10)
                    return title;
                }
            }
        },
		scales: {
			yAxes: [{
				stacked: true
			}],
			xAxes: [{
				stacked: true,
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
				},
	            gridLines: {
	                offsetGridLines: true
	            }
			}]
		}
	};
	const ctx = $("#line_bar_chart");
	var chart = new Chart(ctx, {
		type: "bar",
		data: data,
		options: options
	});
	updateChartColors(chart);
}
