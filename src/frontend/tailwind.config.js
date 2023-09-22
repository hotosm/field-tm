/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{ts,tsx,js,jsx}'],
  theme: {
    extend: {
      colors: {
        primaryRed: '#D73F37',
        primary: {
          50: '#fbecec',
          100: '#f7d9d8',
          200: '#f3c5c5',
          300: '#efb2b2',
          400: '#eb9f9f',
          500: '#e78c8b',
          600: '#e37978',
          700: '#df6565',
          800: '#db5251',
          900: '#d73f3e',
        },
        secondary: {
          50: '#FFF8E3',
          100: '#FFEDB7',
          200: '#FFE28A',
          300: '#FFD85C',
          400: '#FFCE3D',
          500: '#FFC52F',
          600: '#FFB72A',
          700: '#FFA527',
          800: '#FF9525',
          900: '#FF7722',
        },
        grey: {
          50: '#FAFAFA',
          100: '#F5F5F5',
          200: '#E6E6E6',
          300: '#D7D7D7',
          400: '#BDBDBD',
          500: '#989898',
          600: '#757575',
          700: '#616161',
          800: '#484848',
          900: '#212121',
        },
      },
      fontFamily: {
        archivo: ['ArchivoRegular'],
      },
    },
  },
  plugins: [],
  prefix: 'fmtm-',
};
