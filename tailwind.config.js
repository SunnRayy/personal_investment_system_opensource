/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                // SunnRayy brand colors
                'brand-gold': '#D4AF37',
                'brand-gold-light': '#E5C158',
                'brand-gold-dark': '#B8962E',
                'brand-blue': '#3B82F6',
                'brand-blue-dark': '#2563EB',
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
            },
        },
    },
    plugins: [],
}
