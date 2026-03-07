import type { Config } from "tailwindcss";
import defaultTheme from "tailwindcss/defaultTheme";
import tokens from "./design/tokens.json";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    colors: {
      transparent: "transparent",
      current: "currentColor",
      white: tokens.colors.text.primary,
      bg: {
        primary: tokens.colors.bg.primary,
        surface: tokens.colors.bg.surface,
        elevated: tokens.colors.bg.elevated,
        overlay: tokens.colors.bg.overlay
      },
      border: {
        default: tokens.colors.border.default,
        subtle: tokens.colors.border.subtle
      },
      text: {
        primary: tokens.colors.text.primary,
        secondary: tokens.colors.text.secondary,
        muted: tokens.colors.text.muted,
        disabled: tokens.colors.text.disabled,
        inverse: tokens.colors.text.inverse
      },
      semantic: {
        positive: tokens.colors.semantic.positive,
        negative: tokens.colors.semantic.negative,
        warning: tokens.colors.semantic.warning,
        info: tokens.colors.semantic.info,
        neutral: tokens.colors.semantic.neutral
      },
      state: {
        hover: tokens.colors.state.hover,
        active: tokens.colors.state.active,
        selected: tokens.colors.state.selected,
        focusRing: tokens.colors.state.focusRing
      }
    },
    spacing: {
      "0": "0px",
      "4": "4px",
      "8": "8px",
      "12": "12px",
      "16": "16px",
      "20": "20px",
      "24": "24px",
      "32": "32px",
      "40": "40px",
      "48": "48px",
      "64": "64px"
    },
    borderRadius: {
      sm: `${tokens.radii.sm}px`,
      md: `${tokens.radii.md}px`,
      lg: `${tokens.radii.lg}px`,
      pill: `${tokens.radii.pill}px`
    },
    boxShadow: {
      sm: tokens.shadows.sm,
      md: tokens.shadows.md
    },
    fontFamily: {
      sans: ["Inter", ...defaultTheme.fontFamily.sans],
      mono: tokens.typography.fontFamily.mono
    },
    fontSize: {
      ...defaultTheme.fontSize,
      h1: [
        `${tokens.typography.textStyles.h1.fontSize}px`,
        {
          lineHeight: `${tokens.typography.textStyles.h1.lineHeight}px`,
          fontWeight: `${tokens.typography.textStyles.h1.fontWeight}`,
          letterSpacing: `${tokens.typography.textStyles.h1.letterSpacing}px`
        }
      ],
      h2: [
        `${tokens.typography.textStyles.h2.fontSize}px`,
        {
          lineHeight: `${tokens.typography.textStyles.h2.lineHeight}px`,
          fontWeight: `${tokens.typography.textStyles.h2.fontWeight}`,
          letterSpacing: `${tokens.typography.textStyles.h2.letterSpacing}px`
        }
      ],
      h3: [
        `${tokens.typography.textStyles.h3.fontSize}px`,
        {
          lineHeight: `${tokens.typography.textStyles.h3.lineHeight}px`,
          fontWeight: `${tokens.typography.textStyles.h3.fontWeight}`,
          letterSpacing: `${tokens.typography.textStyles.h3.letterSpacing}px`
        }
      ],
      body: [
        `${tokens.typography.textStyles.body.fontSize}px`,
        {
          lineHeight: `${tokens.typography.textStyles.body.lineHeight}px`,
          fontWeight: `${tokens.typography.textStyles.body.fontWeight}`,
          letterSpacing: `${tokens.typography.textStyles.body.letterSpacing}px`
        }
      ],
      label: [
        `${tokens.typography.textStyles.label.fontSize}px`,
        {
          lineHeight: `${tokens.typography.textStyles.label.lineHeight}px`,
          fontWeight: `${tokens.typography.textStyles.label.fontWeight}`,
          letterSpacing: `${tokens.typography.textStyles.label.letterSpacing}px`
        }
      ],
      caption: [
        `${tokens.typography.textStyles.caption.fontSize}px`,
        {
          lineHeight: `${tokens.typography.textStyles.caption.lineHeight}px`,
          fontWeight: `${tokens.typography.textStyles.caption.fontWeight}`,
          letterSpacing: `${tokens.typography.textStyles.caption.letterSpacing}px`
        }
      ],
      mono: [
        `${tokens.typography.textStyles.mono.fontSize}px`,
        {
          lineHeight: `${tokens.typography.textStyles.mono.lineHeight}px`,
          fontWeight: `${tokens.typography.textStyles.mono.fontWeight}`,
          letterSpacing: `${tokens.typography.textStyles.mono.letterSpacing}px`
        }
      ]
    },
    zIndex: {
      base: `${tokens.zIndex.base}`,
      sticky: `${tokens.zIndex.sticky}`,
      dropdown: `${tokens.zIndex.dropdown}`,
      drawer: `${tokens.zIndex.drawer}`,
      modal: `${tokens.zIndex.modal}`,
      toast: `${tokens.zIndex.toast}`
    },
    extend: {
      maxWidth: {
        content: "1440px",
        contentWide: "1560px"
      }
    }
  },
  plugins: []
};

export default config;
