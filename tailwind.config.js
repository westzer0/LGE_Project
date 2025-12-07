/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'lg-red': '#ff456d',
        'lg-beige': '#ece0db',
        'lg-gray': '#f1f1f1',
      },
      fontFamily: {
        'pretendard': ['Pretendard', 'sans-serif'],
        'lg-smart': ['LG Smart_H', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

