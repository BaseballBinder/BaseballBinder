import React from "react";
import ReactApexChart from "react-apexcharts";
import ChartContainer from "./ChartContainer";
import VuiBox from "components/VuiBox";
import VuiTypography from "components/VuiTypography";

/**
 * Donut chart component for card type distribution
 * Uses ApexCharts with Vision UI dark theme
 */
function DonutChart({ title, data, height = "300px" }) {
  // Extract labels and values from data object
  const labels = Object.keys(data || {});
  const series = Object.values(data || {});

  const options = {
    chart: {
      type: 'donut',
      background: 'transparent',
      toolbar: { show: false },
    },
    labels: labels,
    colors: ['#0075ff', '#01b574', '#e31a1a', '#f6ad55', '#9f7aea'],
    theme: { mode: 'dark' },
    legend: {
      position: 'bottom',
      labels: {
        colors: '#a0aec0',
        useSeriesColors: false
      },
      fontSize: '14px',
      fontFamily: 'Plus Jakarta Display, sans-serif',
      markers: {
        radius: 2,
      },
    },
    dataLabels: {
      enabled: true,
      style: {
        fontSize: '14px',
        fontFamily: 'Plus Jakarta Display, sans-serif',
        fontWeight: 'bold',
        colors: ['#fff']
      },
      dropShadow: {
        enabled: false
      }
    },
    plotOptions: {
      pie: {
        donut: {
          size: '70%',
          labels: {
            show: true,
            name: {
              show: true,
              fontSize: '16px',
              fontFamily: 'Plus Jakarta Display',
              color: '#a0aec0',
            },
            value: {
              show: true,
              fontSize: '24px',
              fontFamily: 'Plus Jakarta Display',
              fontWeight: 'bold',
              color: '#ffffff',
              formatter: (val) => val
            },
            total: {
              show: true,
              label: 'Total Cards',
              fontSize: '14px',
              color: '#a0aec0',
              formatter: (w) => {
                return w.globals.seriesTotals.reduce((a, b) => a + b, 0);
              }
            }
          }
        }
      }
    },
    stroke: {
      show: false
    },
    tooltip: {
      theme: 'dark',
      style: {
        fontSize: '12px',
        fontFamily: 'Plus Jakarta Display'
      },
      y: {
        formatter: (val) => `${val} cards`
      }
    }
  };

  // Show empty state if no data
  if (!data || series.length === 0 || series.every(v => v === 0)) {
    return (
      <ChartContainer title={title} height={height}>
        <VuiBox
          display="flex"
          alignItems="center"
          justifyContent="center"
          height="100%"
        >
          <VuiTypography variant="body2" color="text">
            No card data available
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
        type="donut"
        height="100%"
      />
    </ChartContainer>
  );
}

export default DonutChart;
