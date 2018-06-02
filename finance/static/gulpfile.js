var gulp = require("gulp"),//http://gulpjs.com/
	util = require("gulp-util"),//https://github.com/gulpjs/gulp-util
	sass = require("gulp-sass"),//https://www.npmjs.org/package/gulp-sass
	autoprefixer = require("gulp-autoprefixer"),//https://www.npmjs.org/package/gulp-autoprefixer
	minifycss = require("gulp-minify-css"),//https://www.npmjs.org/package/gulp-minify-css
	log = util.log,
	webserver = require("gulp-webserver"),
	nunjucksRender = require("gulp-nunjucks-render"),
	data = require("gulp-data"),
	merge = require("gulp-merge-json");


	gulp.task("server", function() {
		gulp.src("./app")
		.pipe(webserver({
			livereload: true,
			directoryListing: false,
			open: true,
			fallback: "./app/index.html"
		}));
	});


	gulp.task("sass", function(){
		log("Generate css files " + (new Date().toString()));
		gulp.src("./scss/**/*.scss")
		.pipe(sass())
		.pipe(autoprefixer("last 3 version"))
		.pipe(minifycss())
		.pipe(gulp.dest("./app/css"));
	});


	gulp.task("watch-sass", function(){
		gulp.start("sass");
		log("Watching scss files for modifications");
		gulp.watch("./scss/**/*.scss", ["sass"]);
	});


	gulp.task("nunjucks", function() {
		gulp.src("./templates/**.njk")
		.pipe(data(function() {return require("./json/main.json")}))
		.pipe(nunjucksRender({path: ["./templates"]}))
		.pipe(gulp.dest("./app"));
	});


	gulp.task("watch-nunjucks", function() {
		gulp.start("nunjucks");
		log("Watching nunjucks files for modifications");
		gulp.watch(["./templates/**/*.njk", "./json/**/*.json"], ["nunjucks"]);
	});


	gulp.task("json", function() {
		log("json");
		gulp.src(["json/**/*.json", "!./json/main.json"])
		.pipe(merge({
			fileName: "main.json",
		}))
		.pipe(gulp.dest("./json"));
	});


	gulp.task("watch-json", function() {
		gulp.start("json");
		log("Watching json files for modifications");
		gulp.watch(["./json/**/*.json"], ["json"]);
	});


	gulp.task("default", ["watch-sass"]);
