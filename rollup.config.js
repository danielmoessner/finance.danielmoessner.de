import resolve from 'rollup-plugin-node-resolve';
import commonjs from 'rollup-plugin-commonjs'

// export default {
//     input: 'static/javascript/charts.js',
//     output: {
//         file: 'static/app/js/charts.js',
//         name: 'charts',
//         format: 'umd',
//         inlineDynamicImports: true,
//     },
//     plugins: [
//         resolve(),
//         commonjs()
//     ]
// };

export default {
    input: 'static/javascript/app.js',
    output: {
        file: 'static/app/js/app.js',
        format: 'iife',
        inlineDynamicImports: true,
    },
    plugins: [
        resolve(),
        commonjs()
    ]
};