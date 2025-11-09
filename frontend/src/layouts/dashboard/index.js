import React, { useState, useEffect } from "react";
import Grid from "@mui/material/Grid";
import axios from "axios";

// Vision UI components
import VuiBox from "components/VuiBox";
import VuiTypography from "components/VuiTypography";
import DashboardLayout from "examples/LayoutContainers/DashboardLayout";
import DashboardNavbar from "examples/Navbars/DashboardNavbar";
import Footer from "examples/Footer";

// Icons
import { IoWallet } from "react-icons/io5";
import { IoCard } from "react-icons/io5";
import { IoTrendingUp } from "react-icons/io5";
import { IoStatsChart } from "react-icons/io5";

function StatCard({ title, value, icon, color = "info" }) {
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
          background: color === "success"
            ? 'linear-gradient(90deg, transparent, #01b574, transparent)'
            : color === "error"
            ? 'linear-gradient(90deg, transparent, #e31a1a, transparent)'
            : 'linear-gradient(90deg, transparent, #0075ff, transparent)',
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
            background: color === "success"
              ? 'linear-gradient(135deg, #01b574, #35d28a)'
              : color === "error"
              ? 'linear-gradient(135deg, #e31a1a, #ee5d50)'
              : 'linear-gradient(135deg, #0075ff, #3993fe)',
            borderRadius: '12px',
            width: '48px',
            height: '48px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginRight: '12px',
            boxShadow: color === "success"
              ? '0 4px 12px rgba(1, 181, 116, 0.4)'
              : color === "error"
              ? '0 4px 12px rgba(227, 26, 26, 0.4)'
              : '0 4px 12px rgba(0, 117, 255, 0.4)',
          }}
        >
          {icon}
        </VuiBox>
        <VuiTypography variant="caption" color="text" fontWeight="medium">
          {title}
        </VuiTypography>
      </VuiBox>
      <VuiTypography variant="h3" color="white" fontWeight="bold">
        {value}
      </VuiTypography>
    </VuiBox>
  );
}

function Dashboard() {
  const [stats, setStats] = useState({
    total_cards: 0,
    total_value: 0,
    total_invested: 0,
    profit_loss: null,
    has_ebay_data: false
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get("http://127.0.0.1:8000/stats/")
      .then((res) => {
        console.log("📊 Stats:", res.data);
        setStats(res.data);
      })
      .catch((err) => {
        console.error("❌ Error loading stats:", err);
      })
      .finally(() => setLoading(false));
  }, []);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(value);
  };

  const getProfitLossColor = () => {
    if (!stats.profit_loss) return "info";
    return stats.profit_loss >= 0 ? "success" : "error";
  };

  const getProfitLossValue = () => {
    if (stats.profit_loss === null) return "No eBay Data";
    return formatCurrency(Math.abs(stats.profit_loss));
  };

  return (
    <DashboardLayout>
      <DashboardNavbar />
      <VuiBox py={3}>
        <VuiTypography variant="h3" color="white" fontWeight="bold" mb={3}>
          BaseballBinder Dashboard
        </VuiTypography>

        {loading ? (
          <VuiBox textAlign="center" py={5}>
            <VuiTypography variant="h6" color="white">Loading stats...</VuiTypography>
          </VuiBox>
        ) : (
          <Grid container spacing={3}>
            <Grid item xs={12} md={6} lg={3}>
              <StatCard
                title="Total Cards"
                value={stats.total_cards.toLocaleString()}
                icon={<IoCard size="24px" color="white" />}
                color="info"
              />
            </Grid>
            <Grid item xs={12} md={6} lg={3}>
              <StatCard
                title="Collection Value"
                value={formatCurrency(stats.total_value)}
                icon={<IoWallet size="24px" color="white" />}
                color="info"
              />
            </Grid>
            <Grid item xs={12} md={6} lg={3}>
              <StatCard
                title="Total Invested"
                value={formatCurrency(stats.total_invested)}
                icon={<IoStatsChart size="24px" color="white" />}
                color="info"
              />
            </Grid>
            <Grid item xs={12} md={6} lg={3}>
              <StatCard
                title={stats.profit_loss === null ? "Profit/Loss" : stats.profit_loss >= 0 ? "Profit" : "Loss"}
                value={getProfitLossValue()}
                icon={<IoTrendingUp size="24px" color="white" />}
                color={getProfitLossColor()}
              />
            </Grid>
          </Grid>
        )}
      </VuiBox>
      <Footer />
    </DashboardLayout>
  );
}

export default Dashboard;
