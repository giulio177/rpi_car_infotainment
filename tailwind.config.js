// tailwind.config.js
module.exports = {
  darkMode: "class",
  content: ["./gui/html/**/*.html", "./gui/html/**/*.js"], // scansione dei file
  theme: {
    extend: {
      colors: {
        "primary": "#007BFF",
        "background-light": "#f6f7f8",
        "background-dark": "#1E1E1E",
        "surface-dark": "#2A2A2A",
        "text-light": "#EAEAEA",
        "destructive": "#DC3545",
      },
      fontFamily: {
        "display": ["Inter", "sans-serif"],
      },
      borderRadius: {
        "DEFAULT": "0.25rem",
        "lg": "0.5rem",
        "xl": "0.75rem",
        "full": "9999px",
      },
    },
  },
  plugins: [
    require("@tailwindcss/forms"),
    require("@tailwindcss/container-queries"),
  ],
}
