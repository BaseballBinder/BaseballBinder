import React from 'react';
import VuiBox from 'components/VuiBox';
import VuiTypography from 'components/VuiTypography';

/**
 * BaseballBinder custom placeholder for cards without images
 * Matches Vision UI dark theme with baseball card proportions
 */
function CardPlaceholder({ width = 80, height = 110, style = {} }) {
  return (
    <VuiBox
      sx={{
        width: width,
        height: height,
        borderRadius: '10px',
        background: 'linear-gradient(127.09deg, rgba(6, 11, 40, 0.94) 19.41%, rgba(10, 14, 35, 0.8) 76.65%)',
        border: '2px solid rgba(0, 117, 255, 0.15)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
        overflow: 'hidden',
        ...style
      }}
    >
      {/* Baseball diamond watermark background */}
      <VuiBox
        sx={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%) rotate(45deg)',
          width: '60%',
          height: '60%',
          border: '2px solid rgba(0, 117, 255, 0.08)',
          borderRadius: '4px',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: '8px',
            height: '8px',
            background: 'rgba(0, 117, 255, 0.15)',
            borderRadius: '50%',
          }
        }}
      />

      {/* BaseballBinder text */}
      <VuiTypography
        variant="caption"
        sx={{
          fontSize: width > 100 ? '12px' : '9px',
          fontWeight: 'bold',
          color: 'rgba(255, 255, 255, 0.4)',
          textAlign: 'center',
          letterSpacing: '0.5px',
          zIndex: 1,
          textTransform: 'uppercase',
          mb: 0.5
        }}
      >
        BaseballBinder
      </VuiTypography>

      {/* No Image text */}
      <VuiTypography
        variant="caption"
        sx={{
          fontSize: width > 100 ? '10px' : '8px',
          color: 'rgba(255, 255, 255, 0.25)',
          textAlign: 'center',
          zIndex: 1,
        }}
      >
        No Image
      </VuiTypography>

      {/* Decorative baseball icon */}
      <VuiBox
        sx={{
          position: 'absolute',
          bottom: '8px',
          right: '8px',
          width: width > 100 ? '20px' : '14px',
          height: width > 100 ? '20px' : '14px',
          borderRadius: '50%',
          background: 'rgba(255, 255, 255, 0.08)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          '&::before': {
            content: '"⚾"',
            fontSize: width > 100 ? '10px' : '8px',
            opacity: 0.3,
          }
        }}
      />
    </VuiBox>
  );
}

export default CardPlaceholder;
