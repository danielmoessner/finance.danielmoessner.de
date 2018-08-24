jQuery(function(){
	

	// data-toggle dunno for what but i guess it's important
	$(document).ready(function(){
		$('[data-toggle="tooltip"]').tooltip();
	});

	// console
	$(".console--button").click(function(e) {
		$(".console--button").removeClass("console--is-active");
		$(this).addClass("console--is-active");
		$(".console-target").addClass("console--is-hidden");
		var target = $(this).data("target");
		$(target).removeClass("console--is-hidden");
	});

	// not improved at all console 
	// $(document).ready(function() {
	// 	let searchParams = new URLSearchParams(window.location.search)
	// 	if (searchParams.has("console")) {
	// 		let param = searchParams.get("console")
	// 		let button = $("#"+param);
	// 		if (button.length) {
	// 			$(".console--button").removeClass("active");
	// 			$(".console-target").addClass("is-hidden");
	// 			button.addClass("active");
	// 			$(button.data("target")).removeClass("is-hidden");
	// 		}
	// 	}
	// });
});
