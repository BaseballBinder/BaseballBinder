import React, { useEffect, useState } from "react";
import axios from "axios";
import { Dialog, Tabs, Tab, CircularProgress, Skeleton, Slider } from "@mui/material";

import VuiBox from "components/VuiBox";
import VuiTypography from "components/VuiTypography";
import VuiButton from "components/VuiButton";
import VuiAlert from "components/VuiAlert";
import VuiInput from "components/VuiInput";
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
    trackingHistory: [],
    trackingHistoryLoading: false,
    trackingHistoryError: null,
  });
  const [previewEditor, setPreviewEditor] = useState({
    open: false,
    card: null,
    loading: false,
    samples: [],
    selectedUrl: "",
    manualUrl: "",
    fit: "cover",
    focus: 50,
    zoom: 1,
    error: null,
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

  const persistPreview = async (cardId, options = {}) => {
    const {
      previewUrl = null,
      fit = "cover",
      focus = 50,
      zoom = 1,
      clear = false,
    } = options;
    if (!cardId || (!previewUrl && !clear)) return;
    try {
      const res = await axios.post(`http://127.0.0.1:8000/cards/${cardId}/preview`, clear
        ? { clear: true }
        : {
            preview_image_url: previewUrl,
            preview_fit: fit,
            preview_focus: focus,
            preview_zoom: zoom,
          });
      const payload = {
        preview_image_url: res.data.preview_image_url ?? (clear ? null : previewUrl),
        preview_fit: res.data.preview_fit || (clear ? "cover" : fit),
        preview_focus: res.data.preview_focus ?? (clear ? 50 : focus),
        preview_zoom: res.data.preview_zoom ?? (clear ? 1 : zoom),
      };
      setCards((prev) =>
        prev.map((card) =>
          card.id === cardId ? { ...card, ...payload } : card
        )
      );
      setInsights((prev) =>
        prev.card && prev.card.id === cardId
          ? { ...prev, card: { ...prev.card, ...payload }, preview: payload.preview_image_url }
          : prev
      );
    } catch (error) {
      console.error("Failed to persist preview image", error);
    }
  };

  const clearPreview = async (cardId) => {
    await persistPreview(cardId, { clear: true });
  };

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
    if (!card) return;
    setInsights({
      open: true,
      card,
      window: windowValue,
      history: [],
      historyLoading: true,
      preview: card.preview_image_url || null,
      trackingHistory: [],
      trackingHistoryLoading: true,
      trackingHistoryError: null,
    });

    const previewPromise = card.preview_image_url ? Promise.resolve() : fetchPreview(card.id, { persist: true });
    await Promise.all([fetchHistory(card.id, windowValue), previewPromise, fetchTrackingHistory(card.id)]);
  };

  const fetchHistory = async (cardId, windowValue) => {
    if (!cardId) return;
    const targetWindow = windowValue || insights.window || "weekly";
    setInsights((prev) => ({ ...prev, historyLoading: true, window: targetWindow }));
    try {
      const res = await axios.get(`http://127.0.0.1:8000/cards/${cardId}/history?window=${targetWindow}`);
      setInsights((prev) => ({
        ...prev,
        history: res.data.points || [],
        historyLoading: false,
      }));
    } catch (e) {
      setInsights((prev) => ({ ...prev, historyLoading: false }));
    }
  };

  const fetchTrackingHistory = async (cardId) => {
    if (!cardId) return;
    setInsights((prev) => ({ ...prev, trackingHistoryLoading: true, trackingHistoryError: null }));
    try {
      const res = await axios.get(`http://127.0.0.1:8000/cards/${cardId}/tracking-history?limit=10`);
      setInsights((prev) => ({
        ...prev,
        trackingHistory: res.data || [],
        trackingHistoryLoading: false,
      }));
    } catch (e) {
      setInsights((prev) => ({
        ...prev,
        trackingHistoryLoading: false,
        trackingHistoryError: "Failed to load tracking activity.",
      }));
    }
  };

  const fetchPreview = async (cardId, options = {}) => {
    if (!cardId) return null;
    const { persist = false } = options;
    try {
      const res = await axios.get(`http://127.0.0.1:8000/cards/${cardId}/search-with-images`);
      const firstImage = res.data.sample_images?.[0] || res.data.items?.[0]?.image_url || null;
      if (firstImage && persist) {
        await persistPreview(cardId, { previewUrl: firstImage });
      }
      setInsights((prev) => ({ ...prev, preview: firstImage || prev.preview || null }));
      return firstImage;
    } catch (e) {
      setInsights((prev) => ({ ...prev, preview: prev.preview || null }));
      return null;
    }
  };

  const handleWindowChange = (_, value) => {
    if (!insights.card) return;
    setInsights((prev) => ({ ...prev, window: value }));
    fetchHistory(insights.card.id, value);
  };

  const handleFocusChange = (_, newValue) => {
    const value = Array.isArray(newValue) ? newValue[0] : newValue;
    setPreviewEditor((prev) => ({ ...prev, focus: value }));
  };

  const handleZoomChange = (_, newValue) => {
    const value = Array.isArray(newValue) ? newValue[0] : newValue;
    setPreviewEditor((prev) => ({ ...prev, zoom: value }));
  };

  const openPreviewEditor = async (card) => {
    if (!card) return;
    setPreviewEditor({
      open: true,
      card,
      loading: true,
      samples: [],
      selectedUrl: card.preview_image_url || "",
      manualUrl: "",
      fit: card.preview_fit || "cover",
      focus: card.preview_focus ?? 50,
       zoom: card.preview_zoom ?? 1,
      error: null,
    });
    try {
      const res = await axios.get(`http://127.0.0.1:8000/cards/${card.id}/search-with-images`);
      const sampleSet = new Set();
      (res.data?.sample_images || []).forEach((img) => img && sampleSet.add(img));
      (res.data?.items || []).forEach((item) => {
        if (item?.image_url) sampleSet.add(item.image_url);
      });
      const samples = Array.from(sampleSet);
      setPreviewEditor((prev) => ({ ...prev, loading: false, samples }));
    } catch (error) {
      console.error("Failed to load sample images", error);
      setPreviewEditor((prev) => ({ ...prev, loading: false, error: "Unable to load sample images." }));
    }
  };

  const closePreviewEditor = () => {
    setPreviewEditor({
      open: false,
      card: null,
      loading: false,
      samples: [],
      selectedUrl: "",
      manualUrl: "",
      fit: "cover",
      focus: 50,
      zoom: 1,
      error: null,
    });
  };

  const savePreviewFromEditor = async () => {
    if (!previewEditor.card || !previewEditor.selectedUrl) {
      showToast("error", "Select or enter an image before saving.", 3000);
      return;
    }
    await persistPreview(previewEditor.card.id, {
      previewUrl: previewEditor.selectedUrl,
      fit: previewEditor.fit,
      focus: previewEditor.focus,
      zoom: previewEditor.zoom,
    });
    closePreviewEditor();
    showToast("success", "Preview updated");
  };

  const handleSelectPreview = (url) => {
    if (!url) return;
    setPreviewEditor((prev) => ({ ...prev, selectedUrl: url }));
  };

  const handleManualUrlCommit = () => {
    if (!previewEditor.manualUrl) {
      showToast("error", "Enter an image URL first.", 3000);
      return;
    }
    setPreviewEditor((prev) => ({ ...prev, selectedUrl: prev.manualUrl }));
  };

  const handleManualInputChange = (event) => {
    const { value } = event.target;
    setPreviewEditor((prev) => ({ ...prev, manualUrl: value }));
  };

  const handleFitSelect = (value) => {
    setPreviewEditor((prev) => ({ ...prev, fit: value }));
  };

  const handleClearPreview = async () => {
    if (!previewEditor.card) return;
    await clearPreview(previewEditor.card.id);
    setPreviewEditor((prev) => ({
      ...prev,
      selectedUrl: "",
      manualUrl: "",
      fit: "cover",
      focus: 50,
      zoom: 1,
    }));
    showToast("info", "Preview cleared. Pick a new image to replace it.");
  };

  const closeInsights = () => setInsights({
    open: false,
    card: null,
    window: "weekly",
    history: [],
    historyLoading: false,
    preview: null,
    trackingHistory: [],
    trackingHistoryLoading: false,
    trackingHistoryError: null,
  });

  const windowLabels = {
    daily: "Daily",
    weekly: "Weekly",
    monthly: "Monthly",
    lifetime: "All Time",
  };

  const windowDescriptions = {
    daily: "Rolling 7 days of updates (ideal for short bursts of tracking).",
    weekly: "Rolling 30 days to spot near-term trends.",
    monthly: "Rolling 6 months to monitor medium-term performance.",
    lifetime: "Full history since tracking began.",
  };

  const windowRangeFormats = {
    daily: { month: "short", day: "numeric", hour: "numeric" },
    weekly: { month: "short", day: "numeric" },
    monthly: { month: "short", year: "numeric" },
    lifetime: { year: "numeric" },
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

  const purchasePrice =
    typeof insights.card?.price_paid === "number" && !Number.isNaN(insights.card.price_paid)
      ? Number(insights.card.price_paid)
      : null;

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
    chart: { toolbar: { show: false }, zoom: { enabled: false } },
    annotations:
      purchasePrice !== null
        ? {
            yaxis: [
              {
                y: purchasePrice,
                borderColor: "#f5a623",
                strokeDashArray: 5,
                label: {
                  borderColor: "#f5a623",
                  style: { color: "#111", background: "#f5a623" },
                  text: `Purchase $${purchasePrice.toFixed(2)}`,
                },
              },
            ],
            xaxis: [],
            points: [],
            images: [],
            texts: [],
          }
        : undefined,
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
  const currentWindowDescription = windowDescriptions[insights.window] || windowDescriptions.weekly;
  const currentRangeFormat = windowRangeFormats[insights.window] || windowRangeFormats.weekly;
  const previewZoom = insights.card?.preview_zoom ?? 1;
  const historyRangeLabel =
    filteredHistory.length > 1
      ? `${formatDate(filteredHistory[0].t, currentRangeFormat)} - ${formatDate(
          filteredHistory[filteredHistory.length - 1].t,
          currentRangeFormat
        )}`
      : filteredHistory.length === 1
        ? formatDate(filteredHistory[0].t, currentRangeFormat)
        : null;

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
                <VuiBox display="flex" alignItems="center" gap={2}>
                  <VuiBox
                    sx={{
                      width: '48px',
                      height: '68px',
                      borderRadius: '6px',
                      border: card.preview_image_url ? '1px solid rgba(255, 255, 255, 0.1)' : '1px dashed rgba(255, 255, 255, 0.2)',
                      overflow: 'hidden',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: '#a0aec0',
                      fontSize: '10px',
                      textAlign: 'center',
                      px: 1,
                    }}
                  >
                    {card.preview_image_url ? (
                      <VuiBox
                        component="img"
                        src={card.preview_image_url}
                        alt={`${card.player} preview`}
                        sx={{
                          width: '100%',
                          height: '100%',
                          objectFit: card.preview_fit || 'cover',
                          objectPosition: `center ${card.preview_focus ?? 50}%`,
                          transform: `scale(${card.preview_zoom ?? 1})`,
                          transformOrigin: `center ${card.preview_focus ?? 50}%`,
                        }}
                      />
                    ) : (
                      "No image"
                    )}
                  </VuiBox>
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
                <VuiBox display="flex" flexDirection="column" alignItems="center" gap={1}>
                  <VuiButton color="secondary" size="small" onClick={() => openInsights(card)}>
                    View Insights
                  </VuiButton>
                  <VuiButton variant="outlined" color="info" size="small" onClick={() => openPreviewEditor(card)}>
                    Edit Preview
                  </VuiButton>
                </VuiBox>
              </VuiBox>
            ))
          )}
        </VuiBox>

        <Dialog
          open={previewEditor.open}
          onClose={closePreviewEditor}
          maxWidth="md"
          fullWidth
          PaperProps={{
            sx: {
              background: 'linear-gradient(127.09deg, rgba(6, 11, 40, 0.94) 19.41%, rgba(10, 14, 35, 0.94) 76.65%)',
              borderRadius: '15px',
            },
          }}
        >
          <VuiBox p={3}>
            <VuiTypography variant="h4" color="white" fontWeight="bold" mb={1}>
              Edit Preview
            </VuiTypography>
            <VuiTypography variant="body2" color="text" mb={3}>
              Choose the best listing photo, paste your own URL, and adjust how it sits inside the frame.
            </VuiTypography>
            {previewEditor.loading ? (
              <VuiBox display="flex" justifyContent="center" py={4}>
                <CircularProgress sx={{ color: "#0075ff" }} />
              </VuiBox>
            ) : (
              <>
                {previewEditor.error && (
                  <VuiBox mb={2}>
                    <VuiAlert color="error">{previewEditor.error}</VuiAlert>
                  </VuiBox>
                )}
                <VuiTypography variant="caption" color="text" mb={1} sx={{ textTransform: 'uppercase' }}>
                  Sample Images
                </VuiTypography>
                <VuiBox
                  sx={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
                    gap: 2,
                    mb: 3,
                    maxHeight: '220px',
                    overflowY: 'auto',
                  }}
                >
                  {(previewEditor.samples.length ? previewEditor.samples : [previewEditor.card?.preview_image_url]).filter(Boolean).map((img, idx) => (
                    <VuiBox
                      key={`${img}-${idx}`}
                      sx={{
                        border: previewEditor.selectedUrl === img ? '2px solid #0075ff' : '1px solid rgba(255,255,255,0.1)',
                        borderRadius: '10px',
                        padding: '6px',
                        cursor: 'pointer',
                        background: 'rgba(255,255,255,0.03)',
                        transition: 'all 0.2s ease',
                        '&:hover': { border: '2px solid #0075ff' },
                      }}
                      onClick={() => handleSelectPreview(img)}
                    >
                      <VuiBox
                        component="img"
                        src={img}
                        alt="sample preview"
                        sx={{ width: '100%', height: '140px', objectFit: 'cover', borderRadius: '6px' }}
                      />
                      <VuiTypography variant="caption" color="text" display="block" textAlign="center" mt={0.5}>
                        Click to use
                      </VuiTypography>
                    </VuiBox>
                  ))}
                  {previewEditor.samples.length === 0 && (
                    <VuiTypography variant="caption" color="text">
                      No sample images available for this card. Paste a URL below.
                    </VuiTypography>
                  )}
                </VuiBox>
                <VuiBox mb={3}>
                  <VuiTypography variant="caption" color="text" mb={1} display="block" sx={{ textTransform: 'uppercase' }}>
                    Custom Image URL
                  </VuiTypography>
                  <VuiBox display="flex" gap={1}>
                    <VuiInput
                      placeholder="https://..."
                      value={previewEditor.manualUrl}
                      onChange={handleManualInputChange}
                    />
                    <VuiButton color="info" onClick={handleManualUrlCommit}>
                      Use URL
                    </VuiButton>
                  </VuiBox>
                </VuiBox>
                <VuiBox mb={3}>
                  <VuiTypography variant="caption" color="text" mb={1} display="block" sx={{ textTransform: 'uppercase' }}>
                    Fit Mode
                  </VuiTypography>
                  <VuiBox display="flex" gap={1}>
                    <VuiButton
                      size="small"
                      color={previewEditor.fit === "cover" ? "info" : "secondary"}
                      variant={previewEditor.fit === "cover" ? "contained" : "outlined"}
                      onClick={() => handleFitSelect("cover")}
                    >
                      Fill
                    </VuiButton>
                    <VuiButton
                      size="small"
                      color={previewEditor.fit === "contain" ? "info" : "secondary"}
                      variant={previewEditor.fit === "contain" ? "contained" : "outlined"}
                      onClick={() => handleFitSelect("contain")}
                    >
                      Fit
                    </VuiButton>
                  </VuiBox>
                </VuiBox>
                <VuiBox mb={3}>
                  <VuiTypography variant="caption" color="text" mb={1} display="block" sx={{ textTransform: 'uppercase' }}>
                    Vertical Focus ({Math.round(previewEditor.focus)}%)
                  </VuiTypography>
                  <Slider
                    value={previewEditor.focus}
                    min={0}
                    max={100}
                    onChange={handleFocusChange}
                    sx={{ color: '#0075ff' }}
                  />
                </VuiBox>
                <VuiBox mb={3}>
                  <VuiTypography variant="caption" color="text" mb={1} display="block" sx={{ textTransform: 'uppercase' }}>
                    Zoom ({previewEditor.zoom.toFixed(2)}x)
                  </VuiTypography>
                  <Slider
                    value={previewEditor.zoom}
                    min={0.75}
                    max={2.5}
                    step={0.05}
                    onChange={handleZoomChange}
                    sx={{ color: '#0075ff' }}
                  />
                </VuiBox>
                <VuiBox mb={3}>
                  <VuiTypography variant="caption" color="text" mb={1} display="block" sx={{ textTransform: 'uppercase' }}>
                    Live Preview
                  </VuiTypography>
                  <VuiBox
                    sx={{
                      width: '160px',
                      height: '220px',
                      borderRadius: '12px',
                      border: '1px solid rgba(255,255,255,0.1)',
                      overflow: 'hidden',
                      background: 'rgba(255,255,255,0.02)',
                    }}
                  >
                    {previewEditor.selectedUrl ? (
                      <VuiBox
                        component="img"
                        src={previewEditor.selectedUrl}
                        alt="selected preview"
                        sx={{
                          width: '100%',
                          height: '100%',
                          objectFit: previewEditor.fit,
                          objectPosition: `center ${previewEditor.focus}%`,
                          transform: `scale(${previewEditor.zoom})`,
                          transformOrigin: `center ${previewEditor.focus}%`,
                        }}
                      />
                    ) : (
                      <VuiBox
                        sx={{
                          width: '100%',
                          height: '100%',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: '#a0aec0',
                          fontSize: '12px',
                          textAlign: 'center',
                          px: 2,
                        }}
                      >
                        Select or paste an image to preview.
                      </VuiBox>
                    )}
                  </VuiBox>
                </VuiBox>
                <VuiBox display="flex" justifyContent="space-between" gap={1}>
                  <VuiButton color="secondary" variant="outlined" onClick={closePreviewEditor}>
                    Cancel
                  </VuiButton>
                  <VuiButton color="error" variant="outlined" onClick={handleClearPreview} disabled={!previewEditor.card}>
                    Clear Preview
                  </VuiButton>
                  <VuiButton color="info" onClick={savePreviewFromEditor} disabled={!previewEditor.selectedUrl}>
                    Save Preview
                  </VuiButton>
                </VuiBox>
              </>
            )}
          </VuiBox>
        </Dialog>

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
                <VuiBox
                  sx={{
                    width: '80px',
                    height: '112px',
                    borderRadius: '8px',
                    border: insights.preview || insights.card?.preview_image_url ? '2px solid rgba(0, 117, 255, 0.3)' : '2px dashed rgba(255, 255, 255, 0.2)',
                    overflow: 'hidden',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#a0aec0',
                    fontSize: '10px',
                    textAlign: 'center',
                    px: 1,
                  }}
                >
                  {insights.preview || insights.card?.preview_image_url ? (
                    <VuiBox
                      component="img"
                      src={insights.preview || insights.card?.preview_image_url}
                      alt="Card preview"
                      sx={{
                        width: '100%',
                        height: '100%',
                        objectFit: insights.card?.preview_fit || 'cover',
                        objectPosition: `center ${insights.card?.preview_focus ?? 50}%`,
                        transform: `scale(${previewZoom})`,
                        transformOrigin: `center ${insights.card?.preview_focus ?? 50}%`,
                      }}
                    />
                  ) : (
                    "No preview available"
                  )}
                </VuiBox>
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
              {currentWindowDescription} Each update drops a data point into the selected window so you can monitor short and long-term trends.
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
                  {purchasePrice !== null && (
                    <VuiBox textAlign="center">
                      <VuiTypography variant="caption" color="text" mb={0.5}>
                        Purchase Price
                      </VuiTypography>
                      <VuiTypography variant="h5" color="#f5a623" fontWeight="bold">
                        ${purchasePrice.toFixed(2)}
                      </VuiTypography>
                    </VuiBox>
                  )}
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

                {historyRangeLabel && (
                  <VuiTypography variant="caption" color="text" align="center" mb={3}>
                    Window coverage: {historyRangeLabel}
                  </VuiTypography>
                )}

                <VuiBox height="300px">
                  <LineChart
                    lineChartData={historySeries}
                    lineChartOptions={historyOptions}
                  />
                </VuiBox>

                <VuiBox mt={3}>
                  <VuiTypography variant="h6" color="white" fontWeight="bold" mb={2}>
                    Tracking Activity
                  </VuiTypography>
                  {insights.trackingHistoryLoading ? (
                    <Skeleton variant="rectangular" height={80} sx={{ bgcolor: 'rgba(255,255,255,0.05)', borderRadius: '12px' }} />
                  ) : insights.trackingHistoryError ? (
                    <VuiAlert color="warning">{insights.trackingHistoryError}</VuiAlert>
                  ) : insights.trackingHistory?.length ? (
                    insights.trackingHistory.map((entry) => (
                      <VuiBox
                        key={entry.id}
                        display="flex"
                        justifyContent="space-between"
                        alignItems="center"
                        sx={{
                          borderBottom: '1px solid rgba(255,255,255,0.08)',
                          py: 1,
                        }}
                      >
                        <VuiTypography variant="button" color="white" fontWeight="medium">
                          {entry.action === "track" ? "Added to tracking" : "Removed from tracking"}
                        </VuiTypography>
                        <VuiTypography variant="caption" color="text">
                          {new Date(entry.timestamp).toLocaleString()}
                        </VuiTypography>
                      </VuiBox>
                    ))
                  ) : (
                    <VuiTypography variant="caption" color="text">
                      No tracking activity recorded yet.
                    </VuiTypography>
                  )}
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
