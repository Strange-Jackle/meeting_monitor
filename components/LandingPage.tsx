import React, { useEffect, useRef } from 'react';
import { ArrowRight, Zap, Shield, Globe } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { StarsBackground } from './ui/stars-background';

const LandingPage: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    // Check if libraries are loaded
    if (!window.gsap) return;

    // GSAP Intro Animation
    const tl = window.gsap.timeline();

    tl.fromTo(
      titleRef.current,
      { y: 100, opacity: 0, filter: 'blur(10px)' },
      { y: 0, opacity: 1, filter: 'blur(0px)', duration: 1.5, ease: 'power4.out' }
    )
      .fromTo(
        '.hero-tag',
        { y: 20, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.8, stagger: 0.2, ease: 'power3.out' },
        "-=1"
      )
      .fromTo(
        buttonRef.current,
        { scale: 0.8, opacity: 0 },
        { scale: 1, opacity: 1, duration: 1, ease: 'elastic.out(1, 0.3)' },
        "-=0.5"
      );

  }, []);

  return (
    <div ref={containerRef} className="relative w-full h-screen bg-[#05050A] text-white overflow-hidden flex flex-col items-center justify-center">
      {/* Stars Background */}
      <StarsBackground
        starColor="#ffffff"
        speed={30}
        factor={3} // Adjusted density for visual appeal
      />

      {/* Radial Gradient Overlay */}
      <div className="absolute inset-0 bg-gradient-to-t from-[#05050A] via-transparent to-transparent z-10 pointer-events-none"></div>

      {/* Content */}
      <div className="relative z-20 text-center px-4 max-w-4xl mx-auto">
        <div className="flex justify-center gap-4 mb-8">
          <span className="hero-tag flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 text-sm font-medium">
            <Zap size={14} /> Real-time Analytics
          </span>
          <span className="hero-tag flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20 text-sm font-medium">
            <Shield size={14} /> Enterprise Security
          </span>
        </div>

        <h1
          ref={titleRef}
          className="font-display text-7xl md:text-9xl font-black tracking-tighter bg-clip-text text-transparent bg-gradient-to-b from-white to-white/50 mb-8 drop-shadow-2xl"
        >
          Meeting Monitor
        </h1>

        <p className="hero-tag text-lg md:text-xl text-gray-400 mb-12 max-w-2xl mx-auto leading-relaxed">
          The next generation of meeting intelligence. Capture, analyze, and optimize your workflow with AI-driven insights.
        </p>

        <button
          ref={buttonRef}
          onClick={() => navigate('/dashboard')}
          className="group relative inline-flex items-center gap-3 px-8 py-4 bg-white text-black rounded-full text-lg font-semibold hover:bg-gray-100 transition-all active:scale-95"
        >
          <span>Launch Dashboard</span>
          <ArrowRight className="group-hover:translate-x-1 transition-transform" />
          <div className="absolute inset-0 rounded-full ring-2 ring-white/30 animate-ping opacity-50 pointer-events-none"></div>
        </button>
      </div>

      <div className="absolute bottom-10 left-0 right-0 z-20 flex justify-between px-10 text-gray-600 text-xs uppercase tracking-widest pointer-events-none">
        <span>v2.4.0 (Beta)</span>
        <span className="flex items-center gap-2"><Globe size={12} /> Systems Operational</span>
      </div>
    </div>
  );
};

export default LandingPage;