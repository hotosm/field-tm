import React from 'react';
import cardImg from '@/assets/images/project_icon.png';
import logo from '@/assets/images/hotLog.png';
import { LazyLoadImage } from 'react-lazy-load-image-component';

type switcherType = {
  status: 'card' | 'logo';
  width: string | number;
  height?: string | number;
};

type CustomizedImageType = {
  status: 'card' | 'logo';
  style: { width: string | number; height?: string | number };
};

const Switcher = ({ status, width, height }: switcherType) => {
  switch (status) {
    case 'card':
      return <LazyLoadImage src={cardImg} width={width} height={height} alt="Image Alt" effect="blur" />;
    case 'logo':
      return <LazyLoadImage src={logo} width={width} height={height} alt="Image Alt" effect="blur" />;
  }
};

const CustomizedImage = ({ status, style }: CustomizedImageType) => {
  return <Switcher status={status} width={style.width} height={style.height} />;
};

export default CustomizedImage;
