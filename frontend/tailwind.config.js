/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {
      colors: {
        'desktop-primary': '#059669',
        'desktop-secondary': '#10b981',
        'desktop-accent': '#34d399',
      }
    },
  },
  plugins: [],
}

