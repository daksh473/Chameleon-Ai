import React from 'react';

/**
 * SentimentAI Logo — abstract pulse-wave / eye mark.
 * Uses currentColor so it inherits parent text color.
 */
export default function Logo({ className = "w-6 h-6" }) {
  return (
    <svg
      viewBox="0 0 256 256"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Outer eye / lens shape */}
      <path
        d="M128 48C72 48 24 96 8 128c16 32 64 80 120 80s104-48 120-80c-16-32-64-80-120-80Z"
        stroke="currentColor"
        strokeWidth="12"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
      {/* Inner iris ring */}
      <circle
        cx="128"
        cy="128"
        r="40"
        stroke="currentColor"
        strokeWidth="10"
        fill="none"
      />
      {/* Pupil / core dot */}
      <circle cx="128" cy="128" r="16" fill="currentColor" />
      {/* Pulse wave extending right */}
      <path
        d="M176 128h24l12-20 16 40 16-40 12 20h24"
        stroke="currentColor"
        strokeWidth="8"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
        opacity="0.5"
      />
    </svg>
  );
}
