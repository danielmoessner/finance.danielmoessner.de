const source = require("vinyl-source-stream");
const sourcemaps = require("gulp-sourcemaps");
const browserify = require("browserify");
const buffer = require("vinyl-buffer");
const uglify = require("gulp-uglify");
const sass = require("gulp-sass");
const log = require("gulplog");
const gulp = require("gulp");

///
// css
///
function css() {
    return gulp.src("./scss/main.scss")
        .pipe(sourcemaps.init())
        .pipe(sass({
            includePaths: ["node_modules"]
        }))
        .pipe(sourcemaps.write("."))
        .pipe(gulp.dest("./app/css/"))
}

function cssWatch() {
    gulp.watch("./scss/**/*.scss", css)
}

///
// javascript
///
function js(entries, filename) {
    let b = browserify({
        entries: entries,
        debug: true
    });

    return b.bundle()
        .pipe(source(filename))
        .pipe(buffer())
        .pipe(sourcemaps.init({loadMaps: true}))
        .pipe(uglify())
        .on("error", log.error)
        .pipe(sourcemaps.write("./"))
        .pipe(gulp.dest("./app/js/"));
}

function jsApp() {
    return js("./javascript/index.js", "app.js")
}

function jsCharts() {
    return js("./javascript/charts.js", "charts.js")
}

function jsWatch() {
    gulp.watch("./javascript/**.js", gulp.parallel(jsApp, jsCharts))
}

///
// exports
///

gulp.task("watch", gulp.parallel(cssWatch, jsWatch));
gulp.task("js", jsApp);
gulp.task("js:app", jsApp);
gulp.task("js:charts", jsCharts);
gulp.task("css", css);
