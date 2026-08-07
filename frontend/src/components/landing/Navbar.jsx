import React, { useState } from 'react';
import { ChevronDown, Menu, X } from 'lucide-react';
import Logo from './Logo';

export default function Navbar() {
  const [open, setOpen] = useState(false);

  return (
    <nav className="animate-fade-down relative z-20">
      <div className="flex items-center justify-between px-5 sm:px-8 lg:px-10 py-4 sm:py-5">
        {/* Logo */}
        <a href="#" className="flex items-center gap-2 text-white">
          <Logo className="w-5 h-5 sm:w-6 sm:h-6" />
          <span className="text-sm font-medium tracking-tight">SentimentAI</span>
        </a>

        {/* Desktop Nav Links */}
        <div className="hidden md:flex items-center gap-8">
          <a
            href="#features"
            className="flex items-center gap-1 text-[13px] text-gray-300 hover:text-white transition-colors"
          >
            Features
            <ChevronDown className="w-3.5 h-3.5" />
          </a>
          <a
            href="#how-it-works"
            className="text-[13px] text-gray-300 hover:text-white transition-colors"
          >
            How It Works
          </a>
          <a
            href="#pricing"
            className="text-[13px] text-gray-300 hover:text-white transition-colors"
          >
            Pricing
          </a>
        </div>

        {/* Right side */}
        <div className="flex items-center gap-2">
          <a
            href="#"
            className="bg-white text-gray-900 text-[13px] font-medium px-4 sm:px-5 py-2 rounded-full hover:bg-gray-100 transition-colors"
          >
            Get Started
          </a>

          {/* Hamburger */}
          <button
            className="md:hidden flex items-center justify-center w-9 h-9 rounded-full text-white hover:bg-white/10 transition-colors"
            onClick={() => setOpen(!open)}
            aria-label="Toggle menu"
          >
            {open ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Dropdown */}
      {open && (
        <div className="absolute left-4 right-4 top-full rounded-2xl bg-white/80 backdrop-blur-xl ring-1 ring-gray-200 px-5 py-3 animate-fade-up md:hidden">
          <a
            href="#features"
            className="flex items-center justify-between py-3 text-[15px] text-gray-700 hover:text-gray-900 border-b border-gray-200"
            onClick={() => setOpen(false)}
          >
            Features
            <ChevronDown className="w-4 h-4" />
          </a>
          <a
            href="#how-it-works"
            className="block py-3 text-[15px] text-gray-700 hover:text-gray-900 border-b border-gray-200"
            onClick={() => setOpen(false)}
          >
            How It Works
          </a>
          <a
            href="#pricing"
            className="block py-3 text-[15px] text-gray-700 hover:text-gray-900"
            onClick={() => setOpen(false)}
          >
            Pricing
          </a>
        </div>
      )}
    </nav>
  );
}
