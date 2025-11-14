/**
 * ApexCharts Theme Configuration for Vision UI Dashboard
 *
 * This file contains the shared theme configuration for all ApexCharts
 * to ensure consistency with the Vision UI design language.
 *
 * Usage:
 * import { visionUIChartTheme, visionUIColors } from 'utils/apexChartsTheme';
 *
 * <Chart options={{ ...visionUIChartTheme, labels: [...] }} />
 */

// Vision UI Color Palette
export const visionUIColors = {
  primary: '#0075ff',
  success: '#01b574',
  error: '#e31a1a',
  warning: '#f6ad55',
  purple: '#9f7aea',
  text: '#a0aec0',
  white: '#ffffff',
  gradientStart: 'rgba(6, 11, 40, 0.94)',
  gradientEnd: 'rgba(10, 14, 35, 0.49)',
};

// Chart color series (for multi-series charts)
export const chartColors = [
  visionUIColors.primary,
  visionUIColors.success,
  visionUIColors.error,
  visionUIColors.warning,
  visionUIColors.purple,
];

// Base theme configuration for all charts
export const visionUIChartTheme = {
  chart: {
    background: 'transparent',
    fontFamily: 'Roboto, Helvetica, Arial, sans-serif',
    toolbar: {
      show: false,
    },
    foreColor: visionUIColors.text,
  },
  theme: {
    mode: 'dark',
  },
  colors: chartColors,
  grid: {
    borderColor: 'rgba(255, 255, 255, 0.1)',
    strokeDashArray: 4,
    xaxis: {
      lines: {
        show: true,
      },
    },
    yaxis: {
      lines: {
        show: true,
      },
    },
    padding: {
      top: 10,
      right: 10,
      bottom: 10,
      left: 10,
    },
  },
  stroke: {
    curve: 'smooth',
    width: 3,
  },
  dataLabels: {
    enabled: false,
  },
  legend: {
    show: true,
    position: 'bottom',
    horizontalAlign: 'center',
    fontSize: '13px',
    fontWeight: 500,
    labels: {
      colors: visionUIColors.text,
    },
    markers: {
      width: 10,
      height: 10,
      radius: 2,
    },
    itemMargin: {
      horizontal: 10,
      vertical: 5,
    },
  },
  tooltip: {
    theme: 'dark',
    fillSeriesColor: false,
    style: {
      fontSize: '12px',
      fontFamily: 'Roboto, Helvetica, Arial, sans-serif',
    },
    y: {
      formatter: (value) => {
        if (value === null || value === undefined) return 'N/A';
        return value.toLocaleString();
      },
    },
  },
  xaxis: {
    labels: {
      style: {
        colors: visionUIColors.text,
        fontSize: '12px',
        fontWeight: 500,
      },
    },
    axisBorder: {
      show: false,
    },
    axisTicks: {
      show: false,
    },
  },
  yaxis: {
    labels: {
      style: {
        colors: visionUIColors.text,
        fontSize: '12px',
        fontWeight: 500,
      },
    },
  },
};

// Donut Chart specific configuration
export const donutChartOptions = {
  ...visionUIChartTheme,
  chart: {
    ...visionUIChartTheme.chart,
    type: 'donut',
  },
  plotOptions: {
    pie: {
      donut: {
        size: '70%',
        labels: {
          show: true,
          name: {
            show: true,
            fontSize: '14px',
            fontWeight: 600,
            color: visionUIColors.white,
          },
          value: {
            show: true,
            fontSize: '24px',
            fontWeight: 'bold',
            color: visionUIColors.white,
            formatter: (val) => val.toLocaleString(),
          },
          total: {
            show: true,
            showAlways: true,
            label: 'Total',
            fontSize: '14px',
            fontWeight: 600,
            color: visionUIColors.text,
            formatter: (w) => {
              const total = w.globals.seriesTotals.reduce((a, b) => a + b, 0);
              return total.toLocaleString();
            },
          },
        },
      },
    },
  },
  dataLabels: {
    enabled: false,
  },
  legend: {
    ...visionUIChartTheme.legend,
    show: true,
  },
};

// Bar Chart specific configuration
export const barChartOptions = {
  ...visionUIChartTheme,
  chart: {
    ...visionUIChartTheme.chart,
    type: 'bar',
  },
  plotOptions: {
    bar: {
      borderRadius: 8,
      horizontal: false,
      columnWidth: '60%',
      dataLabels: {
        position: 'top',
      },
    },
  },
  dataLabels: {
    enabled: false,
  },
  xaxis: {
    ...visionUIChartTheme.xaxis,
    categories: [],
  },
};

// Horizontal Bar Chart configuration
export const horizontalBarChartOptions = {
  ...barChartOptions,
  plotOptions: {
    bar: {
      borderRadius: 8,
      horizontal: true,
      barHeight: '70%',
    },
  },
};

// Line Chart specific configuration
export const lineChartOptions = {
  ...visionUIChartTheme,
  chart: {
    ...visionUIChartTheme.chart,
    type: 'line',
    zoom: {
      enabled: false,
    },
  },
  stroke: {
    curve: 'smooth',
    width: 3,
  },
  markers: {
    size: 0,
    hover: {
      size: 6,
      sizeOffset: 3,
    },
  },
  xaxis: {
    ...visionUIChartTheme.xaxis,
    type: 'datetime',
  },
  yaxis: {
    ...visionUIChartTheme.yaxis,
  },
  tooltip: {
    ...visionUIChartTheme.tooltip,
    x: {
      format: 'MMM dd, yyyy',
    },
  },
};

// Area Chart configuration
export const areaChartOptions = {
  ...lineChartOptions,
  chart: {
    ...lineChartOptions.chart,
    type: 'area',
  },
  fill: {
    type: 'gradient',
    gradient: {
      shadeIntensity: 1,
      opacityFrom: 0.7,
      opacityTo: 0.2,
      stops: [0, 90, 100],
    },
  },
};

// Sparkline configuration (mini charts)
export const sparklineOptions = {
  chart: {
    type: 'line',
    sparkline: {
      enabled: true,
    },
  },
  stroke: {
    curve: 'smooth',
    width: 2,
  },
  colors: [visionUIColors.primary],
  tooltip: {
    enabled: false,
  },
};

/**
 * Helper function to format currency values in tooltips
 */
export const formatCurrencyTooltip = (value) => {
  if (value === null || value === undefined) return 'N/A';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
  }).format(value);
};

/**
 * Helper function to format percentage values
 */
export const formatPercentage = (value) => {
  if (value === null || value === undefined) return 'N/A';
  return `${value.toFixed(1)}%`;
};

/**
 * Helper function to create gradient background for chart containers
 */
export const chartContainerGradient = {
  background: 'linear-gradient(127.09deg, rgba(6, 11, 40, 0.94) 19.41%, rgba(10, 14, 35, 0.49) 76.65%)',
  borderRadius: '15px',
  padding: '20px',
  boxShadow: '0 8px 26px rgba(0, 0, 0, 0.15), 0 0 20px rgba(0, 117, 255, 0.08)',
  border: '1px solid rgba(255, 255, 255, 0.05)',
};

export default visionUIChartTheme;
