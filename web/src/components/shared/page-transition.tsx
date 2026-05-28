"use client";

import { type ReactNode, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface Props {
  children: ReactNode;
}

export function PageTransition({ children }: Props) {
  const key = useRef(0);
  key.current += 1;

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={key.current}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -8 }}
        transition={{ duration: 0.2, ease: "easeOut" }}
        className="flex flex-1 flex-col"
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}
