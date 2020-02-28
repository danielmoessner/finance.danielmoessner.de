if (process.env.NODE_ENV === "production") {
  module.exports = {
    plugins: [
      require("tailwindcss"),
      require("autoprefixer"),
      require("cssnano")
    ]
  };
} else {
  module.exports = {
    plugins: [require("tailwindcss")]
  };
}
