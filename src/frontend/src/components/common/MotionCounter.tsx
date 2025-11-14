import React, { useEffect, useRef } from 'react';
import { animate } from 'motion';
import { motion } from 'motion/react';

function calculateDuration(count: number) {
  const minDuration = 0.25;
  const maxDuration = 3;
  const speedFactor = 5000;
  const duration = count / speedFactor;
  return Math.min(Math.max(duration, minDuration), maxDuration);
}

export function MotionCounter({ from = 0, to = 1000, duration = 2, hasMore = false }) {
  const ref = useRef<HTMLSpanElement>(null);
  const dur = calculateDuration(to) || duration;

  useEffect(() => {
    if (!ref.current) return;
    animate(from, to, {
      duration: dur,
      ease: 'easeOut',
      onUpdate(latest) {
        ref.current!.textContent = Math.floor(latest).toLocaleString();
      },
    });
  }, [from, to, dur]);

  return (
    <>
      <span ref={ref}>{from}</span>
      {hasMore && (
        <motion.span
          className="fmtm-ml-1"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: dur }}
        >
          +
        </motion.span>
      )}
    </>
  );
}
