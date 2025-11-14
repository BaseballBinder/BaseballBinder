import React from "react";
import ReactApexChart from "react-apexcharts";
import VuiBox from "components/VuiBox";
import VuiTypography from "components/VuiTypography";

/**
 * Enhanced StatCard with sparkline trend chart
 * Shows a stat value with a mini line chart below
 */
function StatCardWithSparkline({ title, value, icon, color = "info", trendData = [] }) {
  const colorMap = {
    info: {
      gradient: 'linear-gradient(135deg, #0075ff, #3993fe)',
      shadow: '0 4px 12px rgba(0, 117, 255, 0.4)',
      border: 'linear-gradient(90deg, transparent, #0075ff, transparent)'
    },
    success: {
      gradient: 'linear-gradient(135deg, #01b574, #35d28a)',
      shadow: '0 4px 12px rgba(1, 181, 116, 0.4)',
      border: 'linear-gradient(90deg, transparent, #01b574, transparent)'
    },
    error: {
      gradient: 'linear-gradient(135deg, #e31a1a, #ee5d50)',
      shadow: '0 4px 12px rgba(227, 26, 26, 0.4)',
      border: 'linear-gradient(90deg, transparent, #e31a1a, transparent)'
    }
  };

  const colors = colorMap[color] || colorMap.info;

  // Sparkline chart options
  const sparklineOptions = {
    chart: {
      type: 'area',
      sparkline: {
        enabled: true
      },
      background: 'transparent',
    },
    stroke: {
      curve: 'smooth',
      width: 2,
      colors: [color === 'success' ? '#01b574' : color === 'error' ? '#e31a1a' : '#0075ff']
    },
    fill: {
      type: 'gradient',
      gradient: {
        shade: 'dark',
        type: 'vertical',
        shadeIntensity: 0.5,
        gradientToColors: [color === 'success' ? '#35d28a' : color === 'error' ? '#ee5d50' : '#3993fe'],
        opacityFrom: 0.4,
        opacityTo: 0.1,
      }
    },
    tooltip: {
      enabled: true,
      theme: 'dark',
      x: {
        show: false
      },
      y: {
        title: {
          formatter: () => ''
        }
      }
    },
    colors: [color === 'success' ? '#01b574' : color === 'error' ? '#e31a1a' : '#0075ff']
  };

  const series = [{
    name: title,
    data: trendData
  }];

  return (
    <VuiBox
      sx={{
        background: 'linear-gradient(127.09deg, rgba(8, 13, 48, 0.92) 19.41%, rgba(10, 14, 35, 0.65) 76.65%)',
        borderRadius: '14px',
        padding: '16px',
        boxShadow: '0 10px 28px rgba(0, 0, 0, 0.25)',
        border: '1px solid rgba(255, 255, 255, 0.04)',
        minHeight: '120px',
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
          background: colors.border,
          opacity: 0.6,
        },

        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.2), 0 0 40px rgba(0, 117, 255, 0.15)',
        },
      }}
    >
      <VuiBox display="flex" alignItems="center" mb={2}>
        <VuiBox
          sx={{
            background: colors.gradient,
            borderRadius: '12px',
            width: '42px',
            height: '42px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginRight: '12px',
            boxShadow: colors.shadow,
          }}
        >
          {icon}
        </VuiBox>
        <VuiTypography variant="caption" color="text" fontWeight="medium">
          {title}
        </VuiTypography>
      </VuiBox>
      <VuiTypography variant="h3" color="white" fontWeight="bold" mb={1}>
        {value}
      </VuiTypography>

      {/* Sparkline Chart */}
      {trendData && trendData.length > 0 && (
        <VuiBox mt={1} sx={{ height: '50px' }}>
          <ReactApexChart
            options={sparklineOptions}
            series={series}
            type="area"
            height="50"
          />
        </VuiBox>
      )}
    </VuiBox>
  );
}

export default StatCardWithSparkline;
