/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#f5f7fb",
        ink: "#172033",
        muted: "#6b7280",
        brand: "#5277e8",
        sidebar: "#111827",
      },
      boxShadow: {
        card: "0 2px 12px rgba(15, 23, 42, 0.045)",
      },
    },
  },
  plugins: [],
};
