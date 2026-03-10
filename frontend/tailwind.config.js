/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'n8n-bg': '#fcfaf7', // light mode background or dark mode '#1e1e1e'
        'n8n-dark': '#2B2B35', 
        'n8n-panel': '#ffffff',
        'n8n-accent': '#FF6E4A', // n8n signature orange
      }
    },
  },
  plugins: [],
}
