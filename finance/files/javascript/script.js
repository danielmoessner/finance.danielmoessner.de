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

	// header navigation fade in
	$(window).scroll(function() {
		if ($(window).scrollTop() > 50.53){
			if (!$(".header").hasClass("fixed-top")) {
				$(".header").css("display", "none");
				$(".header").addClass("fixed-top");
				$("main").css("margin-top", 50.53)
				$(".header").slideDown();
			}			
		} else if ($(window).scrollTop() == 0){
			$(".header").removeClass("fixed-top");
			$("main").css("margin-top", 0)
		};   	
	});

	// start the owl carousel plugin
	$(document).ready(function(){
	  	$(".owl-carousel").owlCarousel({
	  		loop: true,
	  		autoplay: true,
	  		margin: 20,
	  		responsiveClass:true,
	  		dots: false,
		    responsive:{
		        0:{
		            items:1
		        },
		        400:{
		            items:2
		        },
		        1000:{
		            items:3	        
		        }
		    }
	  	});
	});

	// smooth scrolling by clicking on page links
	document.querySelectorAll('a[href^="#"]').forEach(anchor => {
	    anchor.addEventListener('click', function (e) {
	        e.preventDefault();

	        document.querySelector(this.getAttribute('href')).scrollIntoView({
	            behavior: 'smooth'
	        });
	    });
	});


});
