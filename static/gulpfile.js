const gulp = require("gulp");
const sass = require("gulp-sass");
const browserify = require('browserify');
const source = require('vinyl-source-stream');
const buffer = require('vinyl-buffer');
const uglify = require('gulp-uglify');
const sourcemaps = require('gulp-sourcemaps');
const log = require('gulplog');

///
// css
///
function css() {
    return gulp.src('./scss/main.scss')
        .pipe(sourcemaps.init())
        .pipe(sass({
            includePaths: ['node_modules']
        }))
        .pipe(sourcemaps.write('.'))
        .pipe(gulp.dest('./app/css/'))
}

gulp.task("css:watch", function () {
    gulp.watch("./scss/**/*.scss", css)
});

///
// javascript
///
function js() {
    // set up the browserify instance on a task basis
    var b = browserify({
        entries: './javascript/index.js',
        debug: true
    });

    return b.bundle()
        .pipe(source('app.js'))
        .pipe(buffer())
        .pipe(sourcemaps.init({loadMaps: true}))
        // Add transformation tasks to the pipeline here.
        .pipe(uglify())
        .on('error', log.error)
        .pipe(sourcemaps.write('./'))
        .pipe(gulp.dest('./app/js/'));
}

gulp.task("js:watch", function () {
    gulp.watch("./javascript/**.js", js)
});

///
// exports
///

exports.default = gulp.parallel("css:watch", "js:watch");

exports.css = css;
exports.js = js;
