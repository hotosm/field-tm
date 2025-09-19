/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{ts,tsx,js,jsx}'],
  theme: {
    extend: {
      keyframes: {
        'accordion-down': {
          from: { height: '0' },
          to: { height: 'var(--radix-accordion-content-height)' },
        },
        'accordion-up': {
          from: { height: 'var(--radix-accordion-content-height)' },
          to: { height: '0' },
        },
      },
      animation: {
        'accordion-down': 'accordion-down 0.2s ease-out',
        'accordion-up': 'accordion-up 0.2s ease-out',
      },
      colors: {
        red: {
          light: '#FFEDED',
          medium: '#D73F37',
          dark: '#B11E20',
        },
        blue: {
          light: '#929DB3',
          gray: '#68707F',
          dark: '#2C3038',
        },
        orange: '#F2A61D',
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
          100: '#F2F2F2',
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
        barlow: ['Barlow'],
        archivo: ['ArchivoRegular'],
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
  prefix: 'fmtm-',
};
