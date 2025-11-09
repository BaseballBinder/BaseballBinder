import React, { useEffect, useState } from "react";
import axios from "axios";
import { Dialog, Tabs, Tab, CircularProgress, Skeleton } from "@mui/material";

import VuiBox from "components/VuiBox";
import VuiTypography from "components/VuiTypography";
import VuiButton from "components/VuiButton";
import VuiAlert from "components/VuiAlert";
import DashboardLayout from "examples/LayoutContainers/DashboardLayout";
import DashboardNavbar from "examples/Navbars/DashboardNavbar";
import Footer from "examples/Footer";
import LineChart from "examples/Charts/LineCharts/LineChart";

export default function TrackedCollection() {
  const [cards, setCards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [alert, setAlert] = useState({ show: false, type: "", message: "" });
  const [updatingAll, setUpdatingAll] = useState(false);
  const [insights, setInsights] = useState({
    open: false,
    card: null,
    window: "weekly",
    history: [],
    historyLoading: false,
    preview: null,
  });

  const showToast = (type, message, duration = 3000) => {
    setAlert({ show: true, type, message });
    if (duration) {
      setTimeout(() => setAlert({ show: false, type: "", message: "" }), duration);
    }
  };

  const formatDate = (value, options) =>
    value ? new Date(value).toLocaleString([], options || { dateStyle: "medium", timeStyle: "short" }) : "-";

  const fetchTracked = async () => {
    setLoading(true);
    try {
      const res = await axios.get("http://127.0.0.1:8000/cards/tracked/");
      setCards(res.data || []);
    } catch (e) {
      showToast("error", "Failed to load tracked cards", 0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTracked();
  }, []);

  const updateAll = async () => {
    try {
      setUpdatingAll(true);
      await axios.post("http://127.0.0.1:8000/cards/check-tracked-prices");
      await fetchTracked();
      showToast("success", "Tracked card values updated");
    } catch (e) {
      showToast("error", "Failed to update tracked card values", 0);
    } finally {
      setUpdatingAll(false);
    }
  };

  const updateOne = async (id) => {
    try {
      const target = cards.find((c) => c.id === id);
      await axios.post(`http://127.0.0.1:8000/cards/${id}/check-ebay-price`);
      await fetchTracked();
      showToast("success", `${target?.player || "Card"} updated successfully.`);
    } catch (e) {
      showToast("error", "Failed to update card", 0);
    }
  };

  const removeFromTracked = async (id) => {
    try {
      const remaining = cards.filter((card) => card.id !== id);
      await axios.post("http://127.0.0.1:8000/cards/update-tracking", { card_ids: remaining.map((c) => c.id) });
      setCards(remaining);
      showToast("success", "Card removed from tracked.");
    } catch (e) {
      showToast("error", "Failed to remove from tracked", 0);
    }
  };

  const openInsights = async (card, windowValue = "weekly") => {
    setInsights({ open: true, card, window: windowValue, history: [], historyLoading: true, preview: null });
    await Promise.all([fetchHistory(card.id, windowValue), fetchPreview(card.id)]);
  };

  const fetchHistory = async (cardId, windowValue) => {
    if (!cardId) return;
    setInsights((prev) => ({ ...prev, historyLoading: true }));
    try {
      const res = await axios.get(`http://127.0.0.1:8000/cards/${cardId}/history?window=${windowValue}`);
      setInsights((prev) => ({ ...prev, history: res.data.points || [], historyLoading: false }));
    } catch (e) {
      setInsights((prev) => ({ ...prev, historyLoading: false }));
    }
  };

  const fetchPreview = async (cardId) => {
    if (!cardId) return;
    try {
      const res = await axios.get(`http://127.0.0.1:8000/cards/${cardId}/search-with-images`);
      const firstImage = res.data.sample_images?.[0] || res.data.items?.[0]?.image_url;
      setInsights((prev) => ({ ...prev, preview: firstImage || null }));
    } catch (e) {
      setInsights((prev) => ({ ...prev, preview: null }));
    }
  };

  const handleWindowChange = (_, value) => {
    if (!insights.card) return;
    setInsights((prev) => ({ ...prev, window: value }));
    fetchHistory(insights.card.id, value);
  };

  const closeInsights = () => setInsights({ open: false, card: null, window: "weekly", history: [], historyLoading: false, preview: null });

  const windowLabels = {
    daily: "Daily",
    weekly: "Weekly",
    monthly: "Monthly",
    lifetime: "All Time",
  };

  const fallbackHistory = insights.card?.current_value
    ? [{ t: insights.card.last_price_check || new Date().toISOString(), v: insights.card.current_value }]
    : [];

  const normalizedHistory = (insights.history.length ? insights.history : fallbackHistory)
    .map((point) => {
      const rawTimestamp = point?.t || point?.checked_at || point?.timestamp || point?.date;
      const value = point?.v ?? point?.value ?? point?.price;
      if (!rawTimestamp || value === null || value === undefined) return null;
      const timestamp = new Date(rawTimestamp);
      if (Number.isNaN(timestamp.getTime())) return null;
      return { t: timestamp.toISOString(), v: Number(value) };
    })
    .filter(Boolean)
    .sort((a, b) => new Date(a.t) - new Date(b.t));

  const filteredHistory = normalizedHistory;

  const historySeries = filteredHistory.length
    ? [
        {
          name: "Value",
          data: filteredHistory.map((point) => ({ x: point.t, y: point.v })),
        },
      ]
    : [{ name: "Value", data: [] }];

  const formatAxisLabel = (rawValue) => {
    if (rawValue === undefined || rawValue === null) return "";
    const numeric = typeof rawValue === "number" ? rawValue : Number(rawValue);
    const date = Number.isNaN(numeric) ? new Date(rawValue) : new Date(numeric);
    if (Number.isNaN(date.getTime())) return "";
    switch (insights.window) {
      case "daily":
        return date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
      case "weekly":
        return date.toLocaleDateString([], { month: "short", day: "numeric" });
      case "monthly":
        return date.toLocaleDateString([], { month: "short", year: "numeric" });
      default:
        return date.toLocaleDateString([], { year: "numeric", month: "short" });
    }
  };

  const computedTickAmount =
    filteredHistory.length > 1 ? Math.min(filteredHistory.length, 8) : Math.min(Math.max(filteredHistory.length, 1), 4);

  const historyOptions = {
    chart: { toolbar: { show: false } },
    stroke: { curve: "smooth" },
    dataLabels: { enabled: false },
    xaxis: {
      type: "datetime",
      labels: {
        style: { colors: "#c8cfca", fontSize: "10px" },
        datetimeUTC: false,
        formatter: (value, timestamp) => formatAxisLabel(timestamp ?? value),
      },
      tickAmount: computedTickAmount,
    },
    yaxis: { labels: { style: { colors: "#c8cfca", fontSize: "10px" } } },
    tooltip: { theme: "dark" },
    fill: {
      type: "gradient",
      gradient: {
        shade: "dark",
        type: "vertical",
        shadeIntensity: 0,
        inverseColors: true,
        opacityFrom: 0.8,
        opacityTo: 0,
        stops: [],
      },
      colors: ["#0075FF"],
    },
    colors: ["#0075FF"],
  };

  const latestValue = filteredHistory.length ? filteredHistory[filteredHistory.length - 1].v : null;
  const lastTrackedAt = filteredHistory.length
    ? filteredHistory[filteredHistory.length - 1].t
    : insights.card?.last_price_check;
  const lastTrackedLabel = formatDate(lastTrackedAt, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
  const currentWindowLabel = windowLabels[insights.window] || "Custom";

  const percentChange = (() => {
    if (filteredHistory.length < 2) return null;
    const first = filteredHistory[0].v;
    const last = filteredHistory[filteredHistory.length - 1].v;
    if (!first || !last) return null;
    return ((last - first) / first) * 100;
  })();

  const lastTrackedOverall = cards.reduce((latest, card) => {
    if (!card.last_price_check) return latest;
    const timestamp = new Date(card.last_price_check).getTime();
    if (Number.isNaN(timestamp)) return latest;
    return timestamp > latest ? timestamp : latest;
  }, 0);
  const lastTrackedOverallLabel = lastTrackedOverall ? formatDate(lastTrackedOverall) : "No updates yet";

  return (
    <DashboardLayout>
      <DashboardNavbar />
      <VuiBox py={3}>
        <VuiBox
          mb={3}
          display="flex"
          justifyContent="space-between"
          alignItems="center"
          flexWrap="wrap"
          gap={2}
        >
          <VuiBox>
            <VuiTypography variant="h3" color="white" fontWeight="bold" mb={1}>
              Tracked Collection
            </VuiTypography>
            <VuiTypography variant="body2" color="text">
              Manage cards you track for pricing and trends
            </VuiTypography>
          </VuiBox>
          <VuiBox display="flex" flexDirection="column" alignItems="flex-end" gap={0.5}>
            <VuiButton color="info" onClick={updateAll} disabled={updatingAll} sx={{ height: "44px", minWidth: "190px" }}>
              {updatingAll ? "Updating..." : "Update All Tracked"}
            </VuiButton>
            <VuiTypography variant="caption" color="text">
              Last value check: {lastTrackedOverallLabel}
            </VuiTypography>
          </VuiBox>
        </VuiBox>

        {alert.show && (
          <VuiBox mb={3}>
            <VuiAlert color={alert.type === "success" ? "success" : "error"}>{alert.message}</VuiAlert>
          </VuiBox>
        )}

        <VuiBox
          sx={{
            background: 'linear-gradient(127.09deg, rgba(6, 11, 40, 0.94) 19.41%, rgba(10, 14, 35, 0.49) 76.65%)',
            borderRadius: '15px',
            padding: '20px',
            boxShadow: '0px 3.5px 5.5px rgba(0, 0, 0, 0.02)',
          }}
        >
          <VuiBox sx={{ display: 'grid', gridTemplateColumns: '20% 18% 10% 12% 12% 14% 14%', alignItems: 'center', px: 2, py: 1.5, borderBottom: '1px solid rgba(226, 232, 240, 0.1)' }}>
            <VuiTypography variant="caption" color="white" sx={{ textTransform: 'uppercase', fontWeight: 'bold', fontSize: '12px' }}>Player</VuiTypography>
            <VuiTypography variant="caption" color="white" sx={{ textTransform: 'uppercase', fontWeight: 'bold', fontSize: '12px' }}>Set</VuiTypography>
            <VuiTypography variant="caption" color="white" sx={{ textTransform: 'uppercase', fontWeight: 'bold', fontSize: '12px' }}>Year</VuiTypography>
            <VuiTypography variant="caption" color="white" sx={{ textTransform: 'uppercase', fontWeight: 'bold', fontSize: '12px' }}>Current Value</VuiTypography>
            <VuiTypography variant="caption" color="white" sx={{ textTransform: 'uppercase', fontWeight: 'bold', fontSize: '12px' }}>Last Checked</VuiTypography>
            <VuiTypography variant="caption" color="white" sx={{ textTransform: 'uppercase', fontWeight: 'bold', fontSize: '12px', textAlign: 'center' }}>Actions</VuiTypography>
            <VuiTypography variant="caption" color="white" sx={{ textTransform: 'uppercase', fontWeight: 'bold', fontSize: '12px', textAlign: 'center' }}>Insights</VuiTypography>
          </VuiBox>

          {loading ? (
            <VuiBox px={2} py={2}>
              {[...Array(5)].map((_, i) => (
                <VuiBox key={i} sx={{ display: 'grid', gridTemplateColumns: '20% 18% 10% 12% 12% 14% 14%', alignItems: 'center', py: 2 }}>
                  <Skeleton variant="text" sx={{ bgcolor: 'rgba(255, 255, 255, 0.1)' }} />
                  <Skeleton variant="text" sx={{ bgcolor: 'rgba(255, 255, 255, 0.1)' }} />
                  <Skeleton variant="text" sx={{ bgcolor: 'rgba(255, 255, 255, 0.1)' }} />
                  <Skeleton variant="text" sx={{ bgcolor: 'rgba(255, 255, 255, 0.1)' }} />
                  <Skeleton variant="text" sx={{ bgcolor: 'rgba(255, 255, 255, 0.1)' }} />
                  <Skeleton variant="text" sx={{ bgcolor: 'rgba(255, 255, 255, 0.1)' }} />
                  <Skeleton variant="text" sx={{ bgcolor: 'rgba(255, 255, 255, 0.1)' }} />
                </VuiBox>
              ))}
            </VuiBox>
          ) : cards.length === 0 ? (
            <VuiBox px={2} py={4} textAlign="center">
              <VuiTypography variant="body2" color="text">
                No tracked cards yet. Start tracking cards from your collection.
              </VuiTypography>
            </VuiBox>
          ) : (
            cards.map((card) => (
              <VuiBox
                key={card.id}
                sx={{
                  display: 'grid',
                  gridTemplateColumns: '20% 18% 10% 12% 12% 14% 14%',
                  alignItems: 'center',
                  px: 2,
                  py: 2,
                  borderBottom: '1px solid rgba(226, 232, 240, 0.05)',
                  transition: 'all 0.2s ease',
                  '&:hover': {
                    backgroundColor: 'rgba(255, 255, 255, 0.03)',
                  },
                }}
              >
                <VuiBox>
                  <VuiTypography variant="button" color="white" fontWeight="medium">
                    {card.player}
                  </VuiTypography>
                  {card.card_number && (
                    <VuiTypography variant="caption" color="text" display="block">
                      #{card.card_number}
                    </VuiTypography>
                  )}
                </VuiBox>
                <VuiTypography variant="caption" color="text">
                  {card.set_name}
                </VuiTypography>
                <VuiTypography variant="caption" color="text">
                  {card.year}
                </VuiTypography>
                <VuiBox>
                  <VuiTypography variant="button" color="white" fontWeight="medium">
                    ${card.current_value?.toFixed(2) || "N/A"}
                  </VuiTypography>
                </VuiBox>
                <VuiTypography variant="caption" color="text">
                  {formatDate(card.last_price_check)}
                </VuiTypography>
                <VuiBox display="flex" gap={1} justifyContent="center">
                  <VuiButton color="info" size="small" onClick={() => updateOne(card.id)}>
                    Update
                  </VuiButton>
                  <VuiButton color="error" size="small" onClick={() => removeFromTracked(card.id)}>
                    Remove
                  </VuiButton>
                </VuiBox>
                <VuiBox display="flex" justifyContent="center">
                  <VuiButton color="secondary" size="small" onClick={() => openInsights(card)}>
                    View Insights
                  </VuiButton>
                </VuiBox>
              </VuiBox>
            ))
          )}
        </VuiBox>

        <Dialog
          open={insights.open}
          onClose={closeInsights}
          maxWidth="md"
          fullWidth
          PaperProps={{
            sx: {
              background: 'linear-gradient(127.09deg, rgba(6, 11, 40, 0.94) 19.41%, rgba(10, 14, 35, 0.94) 76.65%)',
              backdropFilter: 'blur(42px)',
              borderRadius: '15px',
            },
          }}
        >
          <VuiBox p={3}>
            <VuiBox
              display="flex"
              justifyContent="space-between"
              alignItems="center"
              flexWrap="wrap"
              gap={2}
              mb={3}
            >
              <VuiBox display="flex" alignItems="center" gap={2}>
                {insights.preview ? (
                  <VuiBox
                    component="img"
                    src={insights.preview}
                    alt="Card preview"
                    sx={{
                      width: '80px',
                      height: '112px',
                      objectFit: 'cover',
                      borderRadius: '8px',
                      border: '2px solid rgba(0, 117, 255, 0.3)',
                    }}
                  />
                ) : (
                  <VuiBox
                    sx={{
                      width: '80px',
                      height: '112px',
                      borderRadius: '8px',
                      border: '2px dashed rgba(255, 255, 255, 0.2)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: '#a0aec0',
                      fontSize: '10px',
                      textAlign: 'center',
                      px: 1,
                    }}
                  >
                    No preview available
                  </VuiBox>
                )}
                <VuiBox>
                  <VuiTypography variant="h4" color="white" fontWeight="bold" mb={1}>
                    {insights.card?.player || "Tracked Card"}
                  </VuiTypography>
                  <VuiTypography variant="body2" color="text">
                    {insights.card?.year} {insights.card?.set_name}
                    {insights.card?.card_number && ` #${insights.card.card_number}`}
                  </VuiTypography>
                </VuiBox>
              </VuiBox>
              <VuiButton color="info" onClick={() => insights.card && updateOne(insights.card.id)}>
                Update Value
              </VuiButton>
            </VuiBox>

            <VuiBox mb={2}>
              <Tabs
                value={insights.window}
                onChange={handleWindowChange}
                variant="fullWidth"
                sx={{
                  backgroundColor: 'rgba(255, 255, 255, 0.05)',
                  borderRadius: '12px',
                  '& .MuiTabs-indicator': { backgroundColor: '#0075ff' },
                  '& .MuiTab-root': {
                    color: '#a0aec0',
                    textTransform: 'none',
                    '&.Mui-selected': { color: '#fff' },
                  },
                }}
              >
                <Tab label="Daily" value="daily" />
                <Tab label="Weekly" value="weekly" />
                <Tab label="Monthly" value="monthly" />
                <Tab label="All Time" value="lifetime" />
              </Tabs>
            </VuiBox>

            <VuiTypography variant="button" color="white" fontWeight="medium" mb={0.5}>
              {currentWindowLabel} price history
            </VuiTypography>

            <VuiTypography variant="caption" color="text" mb={3}>
              Each update drops a data point into the selected window so you can monitor short and long-term trends.
            </VuiTypography>

            {insights.historyLoading ? (
              <VuiBox display="flex" justifyContent="center" py={4}>
                <CircularProgress sx={{ color: "#0075ff" }} />
              </VuiBox>
            ) : filteredHistory.length === 0 ? (
              <VuiBox textAlign="center" py={4}>
                <VuiTypography variant="body2" color="text">
                  No price history available for this time window
                </VuiTypography>
              </VuiBox>
            ) : (
              <>
                <VuiBox
                  display="flex"
                  justifyContent="space-around"
                  mb={3}
                  p={2}
                  sx={{
                    background: 'rgba(0, 117, 255, 0.1)',
                    borderRadius: '10px',
                    border: '1px solid rgba(0, 117, 255, 0.3)',
                  }}
                >
                  <VuiBox textAlign="center">
                    <VuiTypography variant="caption" color="text" mb={0.5}>
                      Current Value
                    </VuiTypography>
                    <VuiTypography variant="h5" color="white" fontWeight="bold">
                      ${latestValue?.toFixed(2) || "N/A"}
                    </VuiTypography>
                  </VuiBox>
                  {percentChange !== null && (
                    <VuiBox textAlign="center">
                      <VuiTypography variant="caption" color="text" mb={0.5}>
                        Change
                      </VuiTypography>
                      <VuiTypography
                        variant="h5"
                        fontWeight="bold"
                        sx={{ color: percentChange >= 0 ? "#4caf50" : "#f44336" }}
                      >
                        {percentChange >= 0 ? "+" : ""}
                        {percentChange.toFixed(2)}%
                      </VuiTypography>
                    </VuiBox>
                  )}
                  <VuiBox textAlign="center">
                    <VuiTypography variant="caption" color="text" mb={0.5}>
                      Data Points
                    </VuiTypography>
                    <VuiTypography variant="h5" color="white" fontWeight="bold">
                      {filteredHistory.length}
                    </VuiTypography>
                  </VuiBox>
                  <VuiBox textAlign="center">
                    <VuiTypography variant="caption" color="text" mb={0.5}>
                      Last Tracked
                    </VuiTypography>
                    <VuiTypography variant="button" color="white" fontWeight="medium">
                      {lastTrackedLabel}
                    </VuiTypography>
                  </VuiBox>
                </VuiBox>

                <VuiBox height="300px">
                  <LineChart
                    lineChartData={historySeries}
                    lineChartOptions={historyOptions}
                  />
                </VuiBox>
              </>
            )}

            <VuiBox mt={3} display="flex" justifyContent="flex-end">
              <VuiButton color="secondary" onClick={closeInsights}>
                Close
              </VuiButton>
            </VuiBox>
          </VuiBox>
        </Dialog>
      </VuiBox>
      <Footer />
    </DashboardLayout>
  );
}
