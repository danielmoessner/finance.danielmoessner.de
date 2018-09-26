var gulp = require("gulp"),
	util = require("gulp-util"),
	sass = require("gulp-sass"),
	autoprefixer = require("gulp-autoprefixer"),
	cleanCSS = require("gulp-clean-css"),
	log = util.log,
	concat = require("gulp-concat"),
	minify = require("gulp-minify");


	gulp.task("sass", function(){
		log("Generate css files " + (new Date().toString()));
		return gulp.src("./scss/**/*.scss")
		.pipe(sass())
		.pipe(autoprefixer("last 3 version"))
		.pipe(cleanCSS())
		.pipe(gulp.dest("./app/css"));
	});


	gulp.task("watch-sass", function(){
		gulp.watch("./scss/**/*.scss", gulp.task("sass"))
	});


	gulp.task("javascript", function() {
		log("Generate javascript files " + (new Date().toString()));
	  	return gulp.src([
	  		"./node_modules/jquery/dist/jquery.min.js", 
	  		"./node_modules/chart.js/dist/Chart.bundle.min.js",
	  		"./node_modules/popper.js/dist/umd/popper.min.js",
	  		"./node_modules/bootstrap/dist/js/bootstrap.min.js",
	  		"./node_modules/owl.carousel/dist/owl.carousel.min.js",
	  		"./javascript/**.js"
  		])
	    .pipe(concat("main.js"))
	    // .pipe(minify({
	    // 	ext:{
	    //         src:'-debug.js',
	    //         min:'.js'
	    //     },
	    // }))
	    .pipe(gulp.dest("./app/js"))
	});


	gulp.task("watch-javascript", function() {
		gulp.watch("./javascript/**.js", gulp.task("javascript"))
	});


	gulp.task("default", gulp.parallel("watch-sass", "watch-javascript"));
