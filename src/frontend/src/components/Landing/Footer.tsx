import React from 'react';
import { Link } from 'react-router-dom';
import AssetModules from '@/shared/AssetModules';
import CoreModules from '@/shared/CoreModules';

const socialMedias = [
  { id: 'X', link: 'https://x.com/hotosm', icon: <AssetModules.XIcon className="!fmtm-text-[1.2rem]" /> },
  {
    id: 'LinkedIn',
    link: 'https://www.linkedin.com/company/humanitarian-openstreetmap-team',
    icon: <AssetModules.LinkedInIcon className="!fmtm-text-[1.5rem]" />,
  },
  {
    id: 'Facebook',
    link: 'https://www.facebook.com/hotosm',
    icon: <AssetModules.FacebookIcon className="!fmtm-text-[1.5rem]" />,
  },
  {
    id: 'Instagram',
    link: 'https://www.instagram.com/_hotosm/',
    icon: <AssetModules.InstagramIcon className="!fmtm-text-[1.5rem]" />,
  },
  {
    id: 'YouTube',
    link: 'https://www.youtube.com/user/hotosm',
    icon: <AssetModules.YouTubeIcon className="!fmtm-text-[1.5rem]" />,
  },
  {
    id: 'GitHub',
    link: 'https://github.com/hotosm/field-tm',
    icon: <AssetModules.GitHubIcon className="!fmtm-text-[1.5rem]" />,
  },
];

const Footer = () => {
  const authDetails = CoreModules.useAppSelector((state) => state.login.authDetails);

  return (
    <div className="fmtm-bg-blue-dark fmtm-text-white fmtm-px-[2rem] sm:fmtm-px-[3rem] md:fmtm-px-[4.5rem] fmtm-py-10">
      <div className="fmtm-flex fmtm-gap-4 fmtm-justify-end fmtm-mb-6 sm:fmtm-mb-0">
        <Link to="/explore" className="fmtm-text-base hover:fmtm-text-gray-100">
          Explore Projects
        </Link>
        {authDetails && (
          <Link to="/organization" className="fmtm-text-base hover:fmtm-text-gray-100">
            Organizations
          </Link>
        )}
      </div>
      <div className="fmtm-flex fmtm-flex-col sm:fmtm-flex-row sm:fmtm-items-end sm:fmtm-justify-between fmtm-gap-y-6">
        <div className="fmtm-text-sm">
          <p className="fmtm-mb-1">Want any assistance?</p>
          <p>
            Email:{' '}
            <a href="mailto:tech-data@hotosm.org" className="fmtm-underline">
              tech-data@hotosm.org
            </a>
          </p>
        </div>
        <div className="fmtm-flex fmtm-items-center fmtm-gap-x-[0.5rem]">
          {socialMedias.map((media) => (
            <a key={media.id} href={media.link} target="_blank" rel="noreferrer">
              {media.icon}
            </a>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Footer;
