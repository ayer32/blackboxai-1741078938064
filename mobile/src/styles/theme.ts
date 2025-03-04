import { DefaultTheme } from '@react-navigation/native';

export const colors = {
  // Primary colors with gradients
  primary: {
    light: '#0ea5e9',
    dark: '#38bdf8',
    gradient: ['#0ea5e9', '#38bdf8'],
  },
  // Secondary accent colors
  accent: {
    light: '#818cf8',
    dark: '#a5b4fc',
    gradient: ['#818cf8', '#a5b4fc'],
  },
  // Success states
  success: {
    light: '#10b981',
    dark: '#34d399',
    gradient: ['#10b981', '#34d399'],
  },
  // Error states
  error: {
    light: '#ef4444',
    dark: '#f87171',
    gradient: ['#ef4444', '#f87171'],
  },
  // Warning states
  warning: {
    light: '#f59e0b',
    dark: '#fbbf24',
    gradient: ['#f59e0b', '#fbbf24'],
  },
  // Info states
  info: {
    light: '#3b82f6',
    dark: '#60a5fa',
    gradient: ['#3b82f6', '#60a5fa'],
  },
  // Neutral colors
  neutral: {
    50: '#f9fafb',
    100: '#f3f4f6',
    200: '#e5e7eb',
    300: '#d1d5db',
    400: '#9ca3af',
    500: '#6b7280',
    600: '#4b5563',
    700: '#374151',
    800: '#1f2937',
    900: '#111827',
  },
  // Glass effect colors
  glass: {
    light: 'rgba(255, 255, 255, 0.1)',
    dark: 'rgba(0, 0, 0, 0.1)',
  },
};

export const lightTheme = {
  ...DefaultTheme,
  dark: false,
  colors: {
    primary: colors.primary.light,
    background: colors.neutral[50],
    card: colors.neutral[100],
    text: colors.neutral[900],
    border: colors.neutral[200],
    notification: colors.primary.light,
    glass: colors.glass.light,
    gradient: colors.primary.gradient,
  },
};

export const darkTheme = {
  ...DefaultTheme,
  dark: true,
  colors: {
    primary: colors.primary.dark,
    background: colors.neutral[900],
    card: colors.neutral[800],
    text: colors.neutral[50],
    border: colors.neutral[700],
    notification: colors.primary.dark,
    glass: colors.glass.dark,
    gradient: colors.primary.gradient,
  },
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

export const borderRadius = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  full: 9999,
};

export const typography = {
  fontFamily: {
    sans: 'Inter',
    mono: 'JetBrains Mono',
  },
  fontSize: {
    xs: 12,
    sm: 14,
    base: 16,
    lg: 18,
    xl: 20,
    '2xl': 24,
    '3xl': 30,
    '4xl': 36,
  },
  fontWeight: {
    light: '300',
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
  },
  lineHeight: {
    none: 1,
    tight: 1.25,
    snug: 1.375,
    normal: 1.5,
    relaxed: 1.625,
    loose: 2,
  },
};

export const shadows = {
  sm: {
    light: {
      shadowColor: colors.neutral[900],
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: 0.05,
      shadowRadius: 2,
      elevation: 2,
    },
    dark: {
      shadowColor: colors.neutral[900],
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: 0.1,
      shadowRadius: 2,
      elevation: 2,
    },
  },
  md: {
    light: {
      shadowColor: colors.neutral[900],
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.1,
      shadowRadius: 4,
      elevation: 4,
    },
    dark: {
      shadowColor: colors.neutral[900],
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.15,
      shadowRadius: 4,
      elevation: 4,
    },
  },
  lg: {
    light: {
      shadowColor: colors.neutral[900],
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.1,
      shadowRadius: 8,
      elevation: 8,
    },
    dark: {
      shadowColor: colors.neutral[900],
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.15,
      shadowRadius: 8,
      elevation: 8,
    },
  },
};

export const animations = {
  transition: {
    fast: 200,
    normal: 300,
    slow: 500,
  },
  scale: {
    pressed: 0.95,
  },
  spring: {
    damping: 10,
    mass: 0.3,
    stiffness: 100,
  },
};

export const glassmorphism = {
  light: {
    backgroundColor: 'rgba(255, 255, 255, 0.7)',
    backdropFilter: 'blur(10px)',
    borderColor: 'rgba(255, 255, 255, 0.5)',
  },
  dark: {
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    backdropFilter: 'blur(10px)',
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
};

export const gradients = {
  primary: colors.primary.gradient,
  accent: colors.accent.gradient,
  success: colors.success.gradient,
  error: colors.error.gradient,
  warning: colors.warning.gradient,
  info: colors.info.gradient,
};

export const neuomorphism = {
  light: {
    backgroundColor: colors.neutral[100],
    shadowColor: colors.neutral[900],
    shadowOffset: { width: -4, height: -4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 8,
  },
  dark: {
    backgroundColor: colors.neutral[800],
    shadowColor: colors.neutral[900],
    shadowOffset: { width: -4, height: -4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
};

export const motion = {
  staggered: {
    duration: 300,
    delay: 50,
  },
  fade: {
    in: {
      from: 0,
      to: 1,
      duration: 300,
    },
    out: {
      from: 1,
      to: 0,
      duration: 300,
    },
  },
  slide: {
    up: {
      from: 50,
      to: 0,
      duration: 300,
    },
    down: {
      from: -50,
      to: 0,
      duration: 300,
    },
  },
};

export default {
  colors,
  lightTheme,
  darkTheme,
  spacing,
  borderRadius,
  typography,
  shadows,
  animations,
  glassmorphism,
  gradients,
  neuomorphism,
  motion,
};
