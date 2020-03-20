jQuery(function(){
	

	// data-toggle dunno for what but i guess it's important
	$(document).ready(function(){
		$('[data-toggle="tooltip"]').tooltip();
	});
	
	// console
	$(".console--button").click(function(e) {
		$(".console--button").removeClass("console--is-active");
		$(this).addClass("console--is-active");
		$(".console--target").addClass("console--is-hidden");
		var target = $(this).data("target");
		$(target).removeClass("console--is-hidden");
	});


});


// random hsl color
function semiRandomColor(colorsAmount) {
	var random = Math.floor(Math.random() * 291)  
	colors = []
	var jumper = (291 / colorsAmount)
	for (var i = 0; i < colorsAmount; i++) {
		colors[i] = "hsl(" + Math.round((jumper * i) + 70) + ", 100%, 50%)"
	}
	return colors
}


// update chartjs colors
function updateChartColors(chart){
	var colorChangeValue = 50; //set this to whatever is the deciding color change value
	var datasets = chart.data.datasets;
	var randColor = semiRandomColor(datasets.length);
	for (var i = 0; i < datasets.length; i++) {	
		if (chart.config.type == "line" || chart.config.type == "bar") {
			datasets[i].backgroundColor = randColor[i];
			datasets[i].borderColor = randColor[i];
			datasets[i].pointBorderColor = randColor[i];
			datasets[i].pointBackgroundColor = randColor[i];
			datasets[i].pointHoverBackgroundColor = randColor[i];
			datasets[i].pointHoverBorderColor = randColor[i];
			datasets[i].fill = false;
			datasets[i].pointHoverRadius = 0; // disable line points
			datasets[i].pointRadius = 0;
			datasets[i].pointHitRadius = 15; // disable line points
		} else if (chart.config.type == "pie") {
			datasets[i].backgroundColor = semiRandomColor(datasets[i].data.length);
		}
	}
	chart.update();
}
