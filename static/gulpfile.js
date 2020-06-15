const purgecss = require("@fullhuman/postcss-purgecss");
const sourcemaps = require("gulp-sourcemaps");
const source = require("vinyl-source-stream");
const browserify = require("browserify");
const postcss = require('gulp-postcss');
const buffer = require("vinyl-buffer");
const terser = require('gulp-terser');
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
function js(entries, filename, build) {
    let b1 = browserify({
        entries: entries,
        debug: false
    });

    let b2 = b1.bundle()
        .on("error", log.error)
        .pipe(source(filename))
        .pipe(buffer());

    if (true) {  // instead of !build
        b3 = b2
            .pipe(sourcemaps.init({loadMaps: true}))
            .pipe(sourcemaps.write("./"))
            .pipe(gulp.dest("./app/js/"));
    } else {
        b3 = b2
            .pipe(terser({
                ecma: 2017,
                compress: true,
                output: {
                    comments: false
                }
            }))
            .pipe(gulp.dest("./app/js/"));
    }

    return b3;
}

function jsApp() {
    return js("./javascript/index.js", "app.js", false)
}

function jsCharts() {
    return js("./javascript/charts.js", "charts.js", false)
}

function jsAppBuild() {
    return js("./javascript/index.js", "app.js", true)
}

function jsChartsBuild() {
    return js("./javascript/charts.js", "charts.js", true)
}

function jsWatch() {
    gulp.watch("./javascript/**.js", jsApp)
}

///
// exports
///

gulp.task("watch", gulp.parallel(cssWatch, jsWatch));
gulp.task("js:app", jsApp);
gulp.task("js:charts", jsCharts);
gulp.task("js:build", gulp.parallel(jsAppBuild, jsChartsBuild));
gulp.task("css", css);
gulp.task("css:build", cssBuild);
gulp.task("build", gulp.parallel("js:build", "css:build"));
