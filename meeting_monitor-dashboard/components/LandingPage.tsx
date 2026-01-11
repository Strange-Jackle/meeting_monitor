import React, { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Zap, Shield, Globe } from 'lucide-react';

const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const containerRef = useRef<HTMLDivElement>(null);
  const gridRef = useRef<HTMLDivElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    // Check if libraries are loaded
    if (!window.gsap || !window.anime) return;

    // Anime.js Grid Background Animation
    const gridEl = gridRef.current;
    if (gridEl) {
      gridEl.innerHTML = '';
      const numberOfCells = 100;
      for (let i = 0; i < numberOfCells; i++) {
        const cell = document.createElement('div');
        cell.classList.add('grid-cell');
        cell.style.cssText = `
          width: 100%; 
          height: 100%; 
          border: 1px solid rgba(255,255,255,0.05);
        `;
        gridEl.appendChild(cell);
      }

      window.anime({
        targets: '.grid-cell',
        scale: [
          { value: 0.1, easing: 'easeOutSine', duration: 500 },
          { value: 1, easing: 'easeInOutQuad', duration: 1200 }
        ],
        delay: window.anime.stagger(20, { grid: [10, 10], from: 'center' }),
        loop: true,
        direction: 'alternate',
        easing: 'linear'
      });
    }

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
      {/* Background Grid */}
      <div
        ref={gridRef}
        className="absolute inset-0 grid grid-cols-10 grid-rows-10 opacity-20 pointer-events-none"
        style={{ perspective: '1000px' }}
      ></div>

      {/* Radial Gradient Overlay */}
      <div className="absolute inset-0 bg-gradient-to-t from-[#05050A] via-transparent to-transparent z-10"></div>

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
          className="font-display text-7xl md:text-9xl font-bold tracking-tighter bg-clip-text text-transparent bg-gradient-to-b from-white to-white/50 mb-8"
        >
          Meeting Monitor AI
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

      <div className="absolute bottom-10 left-0 right-0 z-20 flex justify-between px-10 text-gray-600 text-xs uppercase tracking-widest">
        <span>v2.4.0 (Beta)</span>
        <span className="flex items-center gap-2"><Globe size={12} /> Systems Operational</span>
      </div>
    </div>
  );
};

export default LandingPage;