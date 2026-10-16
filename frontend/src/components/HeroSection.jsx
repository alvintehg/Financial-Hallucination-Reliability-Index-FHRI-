import React from 'react';
import LoginForm from './LoginForm';

const HeroSection = () => {
  return (
    <section className="relative w-full min-h-screen bg-dark overflow-hidden">
      {/* Geometric Background Shapes */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Large Blue Triangle - Behind Phones on Right Side */}
        <div
          className="absolute"
          style={{
            top: '10%',
            right: '-10%',
            width: 0,
            height: 0,
            borderLeft: '50vw solid transparent',
            borderBottom: '80vh solid #3B82F6',
            opacity: 0.25,
            zIndex: 1,
          }}
        />

        {/* Semicircle - Bottom Left Corner */}
        <div
          className="absolute bg-primary rounded-full"
          style={{
            bottom: '-30%',
            left: '-15%',
            width: '50vw',
            height: '50vw',
            maxWidth: '800px',
            maxHeight: '800px',
            opacity: 0.2,
            zIndex: 1,
          }}
        />
      </div>

      {/* Main Content Container - Fits on One Page */}
      <div className="relative z-10 max-w-[1504px] mx-auto px-6 md:px-12 lg:px-16 h-screen flex items-center">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12 w-full">

          {/* Left Column - Title & Phone Mockups */}
          <div className="flex flex-col justify-center space-y-6">
            {/* Title & Subtitle */}
            <div className="text-left">
              <h1 className="text-3xl md:text-4xl lg:text-5xl xl:text-6xl font-bold text-white tracking-tight leading-tight mb-3">
                ROBO-ADVISOR
              </h1>
              <p className="text-sm md:text-base lg:text-lg text-gray-300 font-medium leading-relaxed">
                INTELLIGENT FINANCIAL ASSISTANT WITH FHRI RELIABILITY SCORING
              </p>
            </div>

            {/* Phone Mockups */}
            <div className="relative flex justify-start items-center h-[300px] md:h-[350px] lg:h-[400px]">
              {/* Phone Mockup Container */}
              <div className="relative w-full max-w-lg h-full flex items-center justify-start">
                {/* Single Phone Mockup Image (contains multiple phones already) */}
                <div className="relative w-full h-auto">
                  <img
                    src="/hero/AdobeExpress - file.png"
                    alt="Mobile App Interface Mockups"
                    className="w-full h-auto drop-shadow-2xl"
                  />
                </div>

                {/* Glow Effect Behind Phones */}
                <div
                  className="absolute top-1/2 left-1/2 w-64 h-64 bg-primary rounded-full blur-3xl opacity-20"
                  style={{
                    transform: 'translate(-50%, -50%)',
                    zIndex: -1,
                  }}
                />
              </div>
            </div>
          </div>

          {/* Right Column - Login Form */}
          <div className="flex items-center justify-center lg:justify-end">
            <LoginForm />
          </div>
        </div>
      </div>

      {/* Gradient Overlay for Depth */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-dark/50 pointer-events-none" />
    </section>
  );
};

export default HeroSection;
