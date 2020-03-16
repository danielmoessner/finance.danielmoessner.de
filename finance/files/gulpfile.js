const gulp = require("gulp");
const concat = require("gulp-concat");
const minify = require("gulp-minify");
const sass = require("gulp-sass");

///
// css
///
function css() {
    return gulp.src('./scss/main.scss')
        .pipe(sass())
        .pipe(gulp.dest('./app/css/'))
}

gulp.task("css:watch", function () {
    gulp.watch("./scss/**/*.scss", gulp.task("sass"))
});

///
// javascript
///
gulp.task("lm-javascript", function () {
    return gulp.src([
        "./node_modules/jquery/dist/jquery.min.js",
        "./node_modules/chart.js/dist/Chart.bundle.min.js",
        "./node_modules/popper.js/dist/umd/popper.min.js",
        "./node_modules/bootstrap/dist/js/bootstrap.min.js",
        "./javascript/lm_script.js"
    ])
        .pipe(concat("lm_main.js"))
        .pipe(minify({
            ext: {
                src: '_debug.js',
                min: '.js'
            }
        }))
        .pipe(gulp.dest("./app/js"))
});

gulp.task("hmf-javascript", function () {
    return gulp.src([
        "./node_modules/jquery/dist/jquery.min.js",
        "./node_modules/popper.js/dist/umd/popper.min.js",
        "./node_modules/bootstrap/dist/js/bootstrap.min.js",
        "./node_modules/owl.carousel/dist/owl.carousel.min.js",
        "./node_modules/cookieconsent/build/cookieconsent.min.js",
        "./javascript/hmf_script.js"
    ])
        .pipe(concat("hmf_main.js"))
        .pipe(minify({
            ext: {
                src: '_debug.js',
                min: '.js'
            }
        }))
        .pipe(gulp.dest("./app/js"))
});

gulp.task("watch-javascript", function () {
    gulp.watch("./javascript/**.js", gulp.parallel(gulp.task("lm-javascript"), gulp.task("hmf-javascript")))
});

gulp.task("default", gulp.parallel("css:watch", "watch-javascript"));

///
// exports
///
exports.css = css;
