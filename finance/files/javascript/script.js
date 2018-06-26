jQuery(function(){
	

	// data-toggle
	$(document).ready(function(){
		$('[data-toggle="tooltip"]').tooltip();
	});

	// console
	$(".console--button").click(function(e) {
		$(".console--button").removeClass("active");
		$(this).addClass("active");
		$(".console-target").addClass("is-hidden");
		var target = $(this).data("target");
		$(target).removeClass("is-hidden");
	});

});
