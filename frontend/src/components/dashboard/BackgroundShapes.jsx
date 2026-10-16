import React from 'react';

export const BackgroundShapes = () => {
  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none" style={{ zIndex: 0 }}>
      {/* Large Blue Triangle - Top Right */}
      <div
        className="absolute"
        style={{
          top: '-5%',
          right: '-5%',
          width: '600px',
          height: '600px',
          background: 'linear-gradient(135deg, rgba(64, 180, 229, 0.3) 0%, rgba(33, 150, 243, 0.2) 100%)',
          clipPath: 'polygon(100% 0, 100% 100%, 0 0)',
          zIndex: 0,
        }}
      />

      {/* Radial Gradient Circle - Bottom Left */}
      <div
        className="absolute"
        style={{
          bottom: '-15%',
          left: '-10%',
          width: '800px',
          height: '800px',
          background: 'radial-gradient(circle, rgba(64, 180, 229, 0.2) 0%, transparent 70%)',
          zIndex: 0,
        }}
      />

      {/* Triangle Center */}
      <div
        className="absolute"
        style={{
          top: '40%',
          left: '10%',
          width: '400px',
          height: '400px',
          background: 'linear-gradient(225deg, rgba(64, 180, 229, 0.15) 0%, transparent 70%)',
          clipPath: 'polygon(0% 0%, 100% 50%, 0% 100%)',
          zIndex: 0,
        }}
      />

      {/* Semicircle - Right Side */}
      <div
        className="absolute"
        style={{
          top: '30%',
          right: '-10%',
          width: '500px',
          height: '500px',
          background: 'linear-gradient(180deg, rgba(33, 150, 243, 0.15) 0%, transparent 70%)',
          clipPath: 'circle(50% at 0% 50%)',
          zIndex: 0,
        }}
      />

      {/* Blurred Glow Orb 1 */}
      <div
        className="absolute"
        style={{
          top: '20%',
          left: '50%',
          width: '300px',
          height: '300px',
          background: 'radial-gradient(circle, rgba(64, 180, 229, 0.3) 0%, transparent 70%)',
          filter: 'blur(64px)',
          zIndex: 0,
        }}
      />

      {/* Blurred Glow Orb 2 */}
      <div
        className="absolute"
        style={{
          bottom: '30%',
          right: '30%',
          width: '250px',
          height: '250px',
          background: 'radial-gradient(circle, rgba(33, 150, 243, 0.25) 0%, transparent 70%)',
          filter: 'blur(80px)',
          zIndex: 0,
        }}
      />
    </div>
  );
};
