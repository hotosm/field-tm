import React from 'react';
import CoreModules from '@/shared/CoreModules';
import CustomizedImage from '@/utilities/CustomizedImage';

const OrganisationGridCard = ({ filteredData, allDataLength }) => {
  const cardStyle = {
    padding: '20px',
    display: 'flex',
    flexDirection: 'row',
    cursor: 'pointer',
    gap: '20px',
    boxShadow: 'none',
    borderRadius: '0px',
  };
  return (
    <div>
      <p className="fmtm-text-[#9B9999]">
        Showing {filteredData?.length} of {allDataLength} organizations
      </p>
      <div className="fmtm-grid fmtm-grid-cols-1 md:fmtm-grid-cols-2 lg:fmtm-grid-cols-3 fmtm-gap-5">
        {filteredData?.map((data, index) => (
          <CoreModules.Card key={index} sx={cardStyle}>
            {data.logo ? (
              <div className="fmtm-min-w-[60px] md:fmtm-min-w-[80px] lg:fmtm-min-w-[120px]">
                <CoreModules.CardMedia component="img" src={data.logo} sx={{ width: ['60px', '80px', '120px'] }} />
              </div>
            ) : (
              <div className="fmtm-min-w-[60px] fmtm-max-w-[60px] md:fmtm-min-w-[80px] md:fmtm-max-w-[80px] lg:fmtm-min-w-[120px] lg:fmtm-max-w-[120px]">
                <CustomizedImage status={'card'} style={{ width: '100%' }} />
              </div>
            )}

            <CoreModules.Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }} className="fmtm-overflow-hidden">
              <h2
                className="fmtm-line-clamp-1 fmtm-text-base sm:fmtm-text-lg fmtm-font-bold fmtm-capitalize"
                title={data.name}
              >
                {data.name}
              </h2>
              <p
                className="fmtm-line-clamp-3 fmtm-text-[#7A7676] fmtm-font-archivo fmtm-text-sm sm:fmtm-text-base"
                title={data.description}
              >
                {data.description}
              </p>
            </CoreModules.Box>
          </CoreModules.Card>
        ))}
      </div>
    </div>
  );
};
export default OrganisationGridCard;
