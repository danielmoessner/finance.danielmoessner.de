const purgecss = require("@fullhuman/postcss-purgecss");
const sourcemaps = require("gulp-sourcemaps");
const source = require("vinyl-source-stream");
const browserify = require("browserify");
const postcss = require('gulp-postcss');
const buffer = require("vinyl-buffer");
const uglify = require("gulp-uglify");
const cssnano = require("cssnano");
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

function cssBuild() {
    return gulp.src("./scss/main.scss")
        .pipe(sass({
            includePaths: ["node_modules"]
        }))
        .pipe(postcss([
            purgecss({
                content: [
                    "../apps/*/jinja2/*/*.{njk,j2,html}",
                    "../templates/**/*.{njk,j2,html}",
                    "./node_modules/bootstrap/dist/js/bootstrap.js"
                ],
                whitelistPatternsChildren: [/djangoform$/]
            }),
            cssnano()
        ]))
        .pipe(gulp.dest("./app/css/"))
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
gulp.task("css:build", cssBuild);
