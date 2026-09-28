/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#edf5ef',
          100: '#deece1',
          200: '#c2dbc9',
          300: '#97c2a4',
          400: '#65a579',
          500: '#43845e',
          600: '#306e4c',
          700: '#25593e',
          800: '#214a36',
          900: '#1b3a2d',
          950: '#142b22',
        },
      },
      fontFamily: {
        sans: ['DM Sans', 'Aptos', 'sans-serif'],
        display: ['Instrument Serif', 'Georgia', 'serif'],
      },
      fontSize: {
        '2xs': ['0.6875rem', { lineHeight: '1rem' }],
      },
      boxShadow: {
        '2xs': '0 1px 2px rgb(22 37 31 / 0.05)',
      },
    },
  },
  plugins: [],
}
