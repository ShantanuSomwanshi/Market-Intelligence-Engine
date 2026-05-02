/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#07111f",
        panel: "#0f1a2b",
        panelAlt: "#142236",
        accent: "#4da8ff",
        success: "#22c55e",
        danger: "#ef4444",
        warning: "#f59e0b",
        muted: "#94a3b8",
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(77,168,255,0.2), 0 10px 30px rgba(77,168,255,0.15)",
      },
      backgroundImage: {
        grid: "radial-gradient(circle at 1px 1px, rgba(148,163,184,0.18) 1px, transparent 0)",
      },
    },
  },
  plugins: [],
};
