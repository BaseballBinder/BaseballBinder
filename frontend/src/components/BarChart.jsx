import React from "react";
import ReactApexChart from "react-apexcharts";
import ChartContainer from "./ChartContainer";
import VuiBox from "components/VuiBox";
import VuiTypography from "components/VuiTypography";

/**
 * Horizontal bar chart component for distributions
 * Used for team, player, and set distributions
 */
function BarChart({
  title,
  data,
  labelKey = "name",
  valueKey = "count",
  height = "300px",
  horizontal = true,
}) {
  // Extract labels and values from data array
  const labels = data?.map(item => item[labelKey] || item.team || item.player || item.set_name || "Unknown") || [];
  const series = [{
    name: "Cards",
    data: data?.map(item => item[valueKey] || item.count || 0) || []
  }];

  const dataLabelConfig = horizontal
    ? { offsetX: 30, style: { fontSize: '12px', colors: ['#fff'], fontWeight: 'bold' } }
    : { offsetY: -20, style: { fontSize: '12px', colors: ['#fff'], fontWeight: 'bold' } };

  const options = {
    chart: {
      type: 'bar',
      background: 'transparent',
      toolbar: { show: false },
      fontFamily: 'Plus Jakarta Display, sans-serif',
    },
    plotOptions: {
      bar: {
        horizontal,
        borderRadius: 4,
        dataLabels: {
          position: 'top',
        },
      }
    },
    colors: ['#0075ff'],
    dataLabels: {
      enabled: true,
      ...dataLabelConfig,
    },
    stroke: {
      show: true,
      width: 1,
      colors: ['rgba(255, 255, 255, 0.1)']
    },
    xaxis: {
      categories: labels,
      labels: {
        style: {
          colors: '#a0aec0',
          fontSize: '12px',
          fontFamily: 'Plus Jakarta Display',
        }
      },
      axisBorder: {
        show: false
      },
      axisTicks: {
        show: false
      }
    },
    yaxis: {
      labels: {
        style: {
          colors: '#a0aec0',
          fontSize: '12px',
          fontFamily: 'Plus Jakarta Display',
        },
        maxWidth: 150,
      }
    },
    grid: {
      borderColor: 'rgba(255, 255, 255, 0.1)',
      strokeDashArray: 4,
      xaxis: {
        lines: {
          show: true
        }
      },
      yaxis: {
        lines: {
          show: false
        }
      },
    },
    tooltip: {
      theme: 'dark',
      style: {
        fontSize: '12px',
        fontFamily: 'Plus Jakarta Display',
      },
      y: {
        formatter: (val) => `${val} cards`
      }
    },
    theme: {
      mode: 'dark'
    }
  };

  // Show empty state if no data
  if (!data || data.length === 0) {
    return (
      <ChartContainer title={title} height={height}>
        <VuiBox
          display="flex"
          alignItems="center"
          justifyContent="center"
          height="100%"
        >
          <VuiTypography variant="body2" color="text">
            No data available
          </VuiTypography>
        </VuiBox>
      </ChartContainer>
    );
  }

  return (
    <ChartContainer title={title} height={height}>
      <ReactApexChart
        options={options}
        series={series}
        type="bar"
        height="100%"
      />
    </ChartContainer>
  );
}

export default BarChart;
