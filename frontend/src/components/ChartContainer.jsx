import React from "react";
import VuiBox from "components/VuiBox";
import VuiTypography from "components/VuiTypography";

/**
 * Reusable chart container with Vision UI styling
 * Provides consistent styling for all dashboard charts
 */
function ChartContainer({ title, children, height = "300px" }) {
  return (
    <VuiBox
      sx={{
        background: 'linear-gradient(127.09deg, rgba(6, 11, 40, 0.94) 19.41%, rgba(10, 14, 35, 0.49) 76.65%)',
        borderRadius: '15px',
        padding: '20px',
        boxShadow: '0 8px 26px rgba(0, 0, 0, 0.15), 0 0 20px rgba(0, 117, 255, 0.08)',
        backdropFilter: 'blur(120px)',
        border: '1px solid rgba(255, 255, 255, 0.05)',
        height: '100%',
        position: 'relative',
        overflow: 'hidden',
        transition: 'all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)',

        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '2px',
          background: 'linear-gradient(90deg, transparent, #0075ff, transparent)',
          opacity: 0.6,
        },

        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.2), 0 0 40px rgba(0, 117, 255, 0.15)',
        },
      }}
    >
      {title && (
        <VuiBox mb={2}>
          <VuiTypography variant="h6" color="white" fontWeight="bold">
            {title}
          </VuiTypography>
        </VuiBox>
      )}
      <VuiBox sx={{ height: height }}>
        {children}
      </VuiBox>
    </VuiBox>
  );
}

export default ChartContainer;
