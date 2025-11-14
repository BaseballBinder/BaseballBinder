import React from "react";
import ReactApexChart from "react-apexcharts";
import ChartContainer from "./ChartContainer";
import VuiBox from "components/VuiBox";
import VuiTypography from "components/VuiTypography";

/**
 * Line chart component for growth trends
 * Used for collection growth and value trends over time
 */
function LineChart({ title, data, height = "300px" }) {
  // Format data for ApexCharts
  // data should be { card_count: [{date, count}], total_value: [{date, value}] }
  // or a single series: [{date, value}]

  let series = [];
  let categories = [];

  if (Array.isArray(data)) {
    // Single series format
    series = [{
      name: "Value",
      data: data.map(item => item.value || item.count || 0)
    }];
    categories = data.map(item => item.date);
  } else if (data?.card_count && data?.total_value) {
    // Multi-series format from growth-over-time endpoint
    series = [
      {
        name: "Cards Added",
        data: data.card_count.map(item => item.count || 0)
      },
      {
        name: "Value Added ($)",
        data: data.total_value.map(item => item.value || 0)
      }
    ];
    categories = data.card_count.map(item => item.date);
  }

  const options = {
    chart: {
      type: 'line',
      background: 'transparent',
      toolbar: { show: false },
      fontFamily: 'Plus Jakarta Display, sans-serif',
      zoom: {
        enabled: false
      }
    },
    stroke: {
      curve: 'smooth',
      width: 3
    },
    colors: ['#0075ff', '#01b574'],
    theme: { mode: 'dark' },
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
          show: true
        }
      },
    },
    xaxis: {
      type: 'datetime',
      categories: categories,
      labels: {
        style: {
          colors: '#a0aec0',
          fontSize: '12px',
          fontFamily: 'Plus Jakarta Display',
        },
        datetimeFormatter: {
          year: 'yyyy',
          month: 'MMM yyyy',
          day: 'dd MMM',
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
        formatter: (val) => {
          if (val >= 1000) {
            return `${(val / 1000).toFixed(1)}k`;
          }
          return Math.round(val);
        }
      }
    },
    tooltip: {
      theme: 'dark',
      style: {
        fontSize: '12px',
        fontFamily: 'Plus Jakarta Display'
      },
      x: {
        format: 'MMM yyyy'
      },
      y: {
        formatter: (val) => {
          if (typeof val === 'number') {
            return val.toLocaleString();
          }
          return val;
        }
      }
    },
    legend: {
      show: true,
      position: 'top',
      horizontalAlign: 'left',
      labels: {
        colors: '#a0aec0'
      },
      fontSize: '12px',
      fontFamily: 'Plus Jakarta Display',
      markers: {
        radius: 2,
      },
    },
    markers: {
      size: 4,
      colors: ['#0075ff', '#01b574'],
      strokeColors: '#fff',
      strokeWidth: 2,
      hover: {
        size: 6
      }
    }
  };

  // Show empty state if no data
  if (!data || series.length === 0 || series.every(s => s.data.length === 0)) {
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
        type="line"
        height="100%"
      />
    </ChartContainer>
  );
}

export default LineChart;
