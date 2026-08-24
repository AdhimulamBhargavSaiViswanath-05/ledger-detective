/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          light: '#0066CC',
          dark: '#4A9EFF',
        },
        secondary: {
          light: '#00A3E0',
          dark: '#64B5F6',
        },
      },
    },
  },
  plugins: [],
}
