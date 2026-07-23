/**
 * Deep Work Tailwind preset — mirrors the docs.langchain.com "aspen" system.
 * Pair with tokens.css (which defines the CSS custom properties).
 */
export default {
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "rgb(var(--primary) / <alpha-value>)", // #161F34
          light: "rgb(var(--primary-light) / <alpha-value>)", // #7FC8FF
          dark: "rgb(var(--primary-dark) / <alpha-value>)", // #006DDD
        },
        background: { light: "#FFFFFF", dark: "#030710" },
        surface: { raised: "#0D1322", elevated: "#161F34" },
        gray: {
          50: "#F3F3F4",
          100: "#EEEEEF",
          200: "#DFDFE0",
          300: "#CECECF",
          400: "#9F9FA0",
          500: "#707071",
          600: "#505051",
          700: "#3F3F40",
          800: "#262626",
          900: "#171718",
          950: "#0A0B0B",
        },
        success: "rgb(var(--green) / <alpha-value>)",
        warning: "rgb(var(--warning) / <alpha-value>)",
        error: "rgb(var(--error) / <alpha-value>)",
        codeblock: { light: "#eff1f5", dark: "#1e1e2e" },
      },
      fontFamily: {
        heading: ["var(--font-heading)"],
        sans: ["var(--font-body)"],
        mono: ["var(--font-mono)"],
      },
      fontSize: {
        sm: "var(--font-size-sm)",
        lg: "var(--font-size-lg)",
      },
      fontWeight: { emphasis: "var(--font-weight-emphasis)" },
      lineHeight: {
        body: "var(--line-height-body)",
        heading: "var(--line-height-heading)",
      },
      maxWidth: {
        "8xl": "var(--shell-max-width)",
        readable: "var(--measure-readable)",
      },
      minWidth: { "status-body": "var(--measure-status-body-min)" },
      minHeight: { touch: "var(--touch-target-min)" },
      spacing: {
        1: "var(--space-1)",
        2: "var(--space-2)",
        3: "var(--space-3)",
        4: "var(--space-4)",
        navbar: "var(--navbar-height)",
        tabbar: "var(--tabbar-height)",
        header: "calc(var(--navbar-height) + var(--tabbar-height))",
        sidebar: "var(--sidebar-width)",
        rail: "var(--rail-width)",
      },
      borderRadius: {
        tile: "var(--radius-tile)",
        interactive: "var(--radius-interactive)",
        code: "var(--radius-code)",
        frame: "var(--radius-frame)",
      },
      borderWidth: {
        DEFAULT: "var(--border-width-default)",
        control: "var(--border-width-control)",
      },
    },
  },
};
