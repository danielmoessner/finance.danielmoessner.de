jQuery(function(){
	
	
	// cookieconsent
    window.addEventListener("load", function(){
        window.cookieconsent.initialise({
            "palette": {
                    "popup": {
                        "background": "#252830",
                        "text": "#ffffff"
                },
                "button": {
                    "background": "#d09d17",
                    "text": "#000000"
                }
            },
            "theme": "classic",
            "content": {
                "dismiss": "Got it!",
                "link": "Learn More"
            }
        })
    });

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

    // header disappear after nav button clicked
    $(".h-navigation--link").on("click", function() {
        $(".h-navigation--collapse").removeClass("show");
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
