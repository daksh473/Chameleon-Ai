import React from 'react';
import { ArrowUp, Sparkles } from 'lucide-react';
import Navbar from './Navbar';
import DashboardMockup from './DashboardMockup';

export default function Hero({ onStart }) {
  return (
    <section
      className="relative min-h-[100svh] overflow-hidden bg-cover bg-center flex flex-col"
      style={{ backgroundImage: "url('/hero-bg.jpg')" }}
    >
      {/* ── Dark overlay for readability ── */}
      <div className="absolute inset-0 bg-black/40 z-0" />

      {/* ── Navbar ── */}
      <div className="relative z-20">
        <Navbar />
      </div>

      {/* ── Spacer ── */}
      <div className="flex-1 min-h-8 sm:min-h-12 lg:min-h-16 shrink-0" />

      {/* ── Hero Content ── */}
      <div className="relative z-10 flex flex-col items-center text-center px-5">

        {/* Headline */}
        <h1 className="text-white font-normal leading-[1.05] tracking-tight text-[40px] min-[400px]:text-[44px] sm:text-6xl lg:text-7xl xl:text-[80px]">
          <div className="animate-fade-up">Understand emotion.</div>
          <div className="animate-fade-up [animation-delay:100ms]">Act in real time.</div>
        </h1>

        {/* Search / Message Bar */}
        <form
          className="animate-fade-up [animation-delay:220ms] mt-5 sm:mt-6 w-full max-w-xl"
          onSubmit={(e) => { e.preventDefault(); if (onStart) onStart(); }}
        >
          <div className="flex items-center gap-3 rounded-full bg-white/60 backdrop-blur-md ring-1 ring-gray-200 pl-5 pr-1.5 py-1.5">
            <input
              type="text"
              className="flex-1 bg-transparent text-sm sm:text-base text-gray-900 placeholder-gray-500 outline-none py-2"
              placeholder="Type a customer message to analyze..."
            />
            <button
              type="submit"
              className="w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-gray-900 text-white hover:scale-105 active:scale-95 transition-transform shrink-0 flex items-center justify-center"
            >
              <ArrowUp className="w-4 h-4 sm:w-[18px] sm:h-[18px]" />
            </button>
          </div>
        </form>

        {/* Description */}
        <p className="animate-fade-up [animation-delay:340ms] mt-4 sm:mt-5 text-gray-300 text-sm sm:text-base lg:text-lg leading-relaxed max-w-md">
          Detect sentiment, auto-escalate frustration, and trigger upsells —
          <br />
          powered by AI that responds in under{' '}
          <Sparkles className="inline w-4 h-4 -mt-1" /> 1 second
        </p>

        {/* CTA Buttons */}
        <div className="animate-fade-up [animation-delay:460ms] mt-4 sm:mt-5 flex flex-wrap items-center justify-center gap-3">
          <button
            onClick={onStart}
            className="bg-white text-gray-900 text-sm font-medium px-6 py-2.5 rounded-full hover:bg-gray-100 hover:shadow-lg transition-all"
          >
            See Live Demo
          </button>
          <a
            href="https://github.com/daksh473/Chameleon-Ai"
            target="_blank"
            rel="noopener noreferrer"
            className="text-gray-300 text-sm font-medium px-6 py-2.5 rounded-full ring-1 ring-white/30 hover:bg-white/10 transition-colors"
          >
            View on GitHub
          </a>
        </div>
      </div>

      {/* ── Spacer ── */}
      <div className="flex-1 min-h-10 sm:min-h-12 lg:min-h-16 shrink-0" />

      {/* ── Dashboard Mockup ── */}
      <div className="relative z-10">
        <DashboardMockup />
      </div>

      {/* ── Ambient Glow Overlay (bottom) ── */}
      <div
        className="pointer-events-none absolute bottom-0 left-0 z-10 w-full select-none"
        style={{ height: '30%' }}
      >
        <div
          className="w-full h-full"
          style={{
            background: 'radial-gradient(ellipse 80% 100% at 50% 100%, rgba(91,139,247,0.15) 0%, rgba(91,139,247,0.05) 40%, transparent 70%)',
          }}
        />
      </div>
    </section>
  );
}
