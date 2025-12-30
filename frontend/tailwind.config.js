/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#fef2f2',
          100: '#fee2e2',
          200: '#fecaca',
          300: '#fca5a5',
          400: '#f87171',
          500: '#ef4444',
          600: '#dc2626',
          700: '#b91c1c',
          800: '#991b1b',
          900: '#7f1d1d',
        },
        dark: {
          bg: '#121212',
          card: '#1e1e1e',
          border: '#2e2e2e',
        },
        staff: {
          manager: '#990000',
          'staff-manager': '#F04000',
          'assistant-sm': '#8900F0',
          'snr-admin': '#d207d3',
          admin: '#FA1E8A',
          'snr-moderator': '#15c000',
          moderator: '#4a86e8',
          'snr-operator': '#38761d',
          operator: '#93c47d',
          't-staff': '#b6d7a8',
        },
      },
    },
  },
  plugins: [],
};
