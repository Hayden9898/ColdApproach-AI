import type { Transition, Variants } from "framer-motion";

export const DURATION = {
  fast: 0.15,
  normal: 0.2,
  slow: 0.3,
} as const;

export const EASE = {
  out: [0.25, 0.1, 0.25, 1] as const,
  inOut: [0.42, 0, 0.58, 1] as const,
};

export const SPRING: Transition = {
  type: "spring",
  stiffness: 400,
  damping: 30,
};

export const fadeIn: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
};

export const slideUp: Variants = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -8 },
};

export const slideRight: Variants = {
  initial: { opacity: 0, x: -12 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: 12 },
};
