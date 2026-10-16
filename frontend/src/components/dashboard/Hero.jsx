import React from 'react';

export const Hero = ({ showMarketBadge = true, activeTab = 'dashboard' }) => {
  const isAdvisorPage = activeTab === 'advisor';

  return (
    <div className={`relative overflow-hidden ${isAdvisorPage ? 'px-8 py-8' : 'px-8 py-12'}`}>
      {/* Decorative Blue Triangles - Hide on advisor page for cleaner look */}
      {!isAdvisorPage && (
        <>
          <div
            className="absolute"
            style={{
              top: '10%',
              right: '20%',
              width: '150px',
              height: '150px',
              background: 'linear-gradient(135deg, rgba(64, 180, 229, 0.3) 0%, rgba(33, 150, 243, 0.2) 100%)',
              clipPath: 'polygon(50% 0%, 100% 100%, 0% 100%)',
              zIndex: 1,
            }}
          />
          <div
            className="absolute"
            style={{
              bottom: '15%',
              left: '15%',
              width: '100px',
              height: '100px',
              background: 'linear-gradient(225deg, rgba(64, 180, 229, 0.25) 0%, transparent 70%)',
              clipPath: 'polygon(50% 0%, 100% 100%, 0% 100%)',
              zIndex: 1,
            }}
          />
        </>
      )}

      {/* Content */}
      <div className="relative z-10">
        {/* Status Badge - Only show on non-advisor pages if enabled */}
        {showMarketBadge && !isAdvisorPage && (
          <div className="flex items-center gap-2 mb-6">
            <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-black bg-opacity-40 border border-green-500 border-opacity-30">
              <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              <span className="text-sm font-semibold text-green-400 tracking-wide">MARKET OPEN</span>
            </div>
          </div>
        )}

        {/* Main Title - Full width on advisor page */}
        <h1 className={`font-bold tracking-wider text-white ${isAdvisorPage ? 'text-5xl sm:text-6xl mb-3' : 'text-6xl mb-4'}`} style={{ textTransform: 'uppercase' }}>
          ROBO-ADVISOR
        </h1>

        {/* Description */}
        <p className={`text-white text-opacity-70 leading-relaxed ${isAdvisorPage ? 'text-base' : 'text-lg max-w-2xl'}`}>
          AI-Powered Wealth Management with Real-Time Market Intelligence & FHRI Reliability Scoring
        </p>
      </div>
    </div>
  );
};
