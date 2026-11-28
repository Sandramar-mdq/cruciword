module.exports = {
  content: ["./templates/**/*.html", "./static/js/**/*.js"],
  theme: {
    extend: {
      colors: {
        cw: {
          bg: "var(--cw-bg)",
          card: "var(--cw-card)",
          ink: "var(--cw-ink)",
          outline: "var(--cw-outline)",
          accent: "var(--cw-accent)",
        },
      },
      fontFamily: {
        cw: ['"Balsamiq Sans"', '"Trebuchet MS"', "sans-serif"],
      },
    },
  },
  plugins: [],
};
