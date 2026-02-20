/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        'ibm-plex-kr': ['IBM Plex Sans KR', 'sans-serif'],
        'noto-sans-kr': ['Noto Sans KR', 'sans-serif'],
        'ibm-plex': ['IBM Plex Sans', 'sans-serif'],
        'nanum-gothic': ['Nanum Gothic', 'sans-serif'],
      },
      colors: {
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
        }
      }
    },
  },
  plugins: [],
}
