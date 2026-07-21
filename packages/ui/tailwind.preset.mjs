/**
 * Deep Work Tailwind preset — mirrors the docs.langchain.com "aspen" system.
 * Pair with tokens.css (which defines the CSS custom properties).
 */
export default {
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: 'rgb(var(--primary) / <alpha-value>)',      // #161F34
          light: 'rgb(var(--primary-light) / <alpha-value>)',  // #7FC8FF
          dark: 'rgb(var(--primary-dark) / <alpha-value>)',    // #006DDD
        },
        background: { light: '#FFFFFF', dark: '#030710' },
        surface: { raised: '#0D1322', elevated: '#161F34' },
        gray: {
          50: '#F3F3F4', 100: '#EEEEEF', 200: '#DFDFE0', 300: '#CECECF',
          400: '#9F9FA0', 500: '#707071', 600: '#505051', 700: '#3F3F40',
          800: '#262626', 900: '#171718', 950: '#0A0B0B',
        },
        success: 'rgb(var(--green) / <alpha-value>)',
        warning: 'rgb(var(--warning) / <alpha-value>)',
        error: 'rgb(var(--error) / <alpha-value>)',
        codeblock: { light: '#eff1f5', dark: '#1e1e2e' },
      },
      fontFamily: {
        heading: ['Inter', 'system-ui', 'sans-serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'monospace'],
      },
      maxWidth: { '8xl': '92rem' },
      spacing: {
        navbar: '3.5rem', tabbar: '2.5rem', header: '6rem',
        sidebar: '18rem', rail: '19rem',
      },
      borderRadius: {
        tile: '0.5rem', interactive: '0.75rem',
        code: '14px', frame: '1rem',
      },
    },
  },
}
