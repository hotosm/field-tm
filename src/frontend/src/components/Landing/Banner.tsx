import React from 'react';
import { useNavigate } from 'react-router-dom';
import landingbg from '@/assets/images/landing-bg.jpg';
import Button from '@/components/common/Button';
import { motion } from 'motion/react';

const Banner = () => {
  const navigate = useNavigate();
  const title = 'FIELD - TASKING MANAGER';
  const description = 'Enhancing field mapping efficiency and accuracy through seamless coordination';

  return (
    <div
      style={{ backgroundImage: `url(${landingbg})` }}
      className={`fmtm-w-full fmtm-h-[38rem] fmtm-bg-no-repeat fmtm-bg-cover fmtm-relative fmtm-flex fmtm-items-center`}
    >
      <div className="fmtm-absolute fmtm-left-0 fmtm-top-0 fmtm-w-full fmtm-h-full fmtm-bg-black/40" />
      <div className="fmtm-text-white fmtm-z-50 fmtm-relative fmtm-ml-[10%] fmtm-flex fmtm-flex-col fmtm-gap-y-5">
        <h1>
          {title.split(' ').map((text, i) => (
            <motion.span
              key={i}
              initial={{ y: 20, opacity: 0, filter: 'blur(5px)' }}
              animate={{ y: 0, opacity: 1, filter: 'none' }}
              transition={{
                delay: i * 0.2,
              }}
              className="fmtm-inline-block"
            >
              {text}&nbsp;
            </motion.span>
          ))}
        </h1>
        <h4 className="!fmtm-max-w-[400px]">
          {description.split(' ').map((text, i) => (
            <motion.span
              key={i}
              initial={{ y: 5, opacity: 0, filter: 'blur(5px)' }}
              animate={{ y: 0, opacity: 1, filter: 'none' }}
              transition={{
                delay: i * 0.1,
              }}
              className="fmtm-inline-block"
            >
              {text}&nbsp;
            </motion.span>
          ))}
        </h4>
        <motion.div whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }} className="fmtm-w-fit">
          <Button variant="primary-red" onClick={() => navigate('/explore')}>
            EXPLORE PROJECTS
          </Button>
        </motion.div>
      </div>
    </div>
  );
};

export default Banner;
