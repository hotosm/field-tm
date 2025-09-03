import React from 'react';
import Banner from '@/components/Landing/Banner';
import About from '@/components/Landing/About';
import Features from '@/components/Landing/Features';
import UseCase from '@/components/Landing/UseCase';
import Footer from '@/components/Landing/Footer';

const Landing = () => {
  return (
    <div className="fmtm-w-[100vw] fmtm-overflow-x-hidden fmtm-grid fmtm-gap-[6rem]">
      <Banner />
      <About />
      <Features />
      <UseCase />
      <Footer />
    </div>
  );
};

export default Landing;
