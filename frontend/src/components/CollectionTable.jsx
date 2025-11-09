import React, { useEffect, useState } from "react";
import axios from "axios";
import { Table, TableBody, TableCell, TableHead, TableRow, CircularProgress, Dialog, DialogTitle, DialogContent, DialogActions, TableContainer, Skeleton } from "@mui/material";
import VuiBox from "components/VuiBox";
import VuiTypography from "components/VuiTypography";
import VuiAlert from "components/VuiAlert";
import VuiButton from "components/VuiButton";
import VuiInput from "components/VuiInput";
import { Grid } from "@mui/material";

export default function CollectionTable() {
  const [cards, setCards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [alert, setAlert] = useState({ show: false, type: "", message: "" });
  const [filters, setFilters] = useState({
    set_name: "",
    player: "",
    year: "",
  });
  const [ebayDialog, setEbayDialog] = useState({
    open: false,
    loading: false,
    data: null,
    error: null,
    cardId: null,
    showRefinementHelp: false,
  });
  const [trackedIds, setTrackedIds] = useState(new Set());
  const [trackingLoading, setTrackingLoading] = useState(true);

  const showTemporaryAlert = (type, message, duration = 3000) => {
    setAlert({ show: true, type, message });
    if (duration) {
      setTimeout(() => {
        setAlert({ show: false, type: "", message: "" });
      }, duration);
    }
  };

  const fetchCards = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = {};
      if (filters.set_name) params.set_name = filters.set_name;
      if (filters.player) params.player = filters.player;
      if (filters.year) params.year = filters.year;

      const res = await axios.get("http://127.0.0.1:8000/cards/", { params });
      console.log("📦 Cards loaded:", res.data);
      setCards(res.data || []);
    } catch (err) {
      console.error("❌ Error loading cards:", err);
      setError("Failed to load cards. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCards();
    loadTrackedCards();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleFilterChange = (e) => {
    setFilters((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSearch = () => {
    fetchCards();
  };

  const handleClearFilters = () => {
    setFilters({ set_name: "", player: "", year: "" });
    setTimeout(() => fetchCards(), 100);
  };

  const handleDeleteCard = async (cardId) => {
    if (!window.confirm("Are you sure you want to delete this card?")) {
      return;
    }

    try {
      await axios.delete(`http://127.0.0.1:8000/cards/${cardId}`);
      setCards((prev) => prev.filter((card) => card.id !== cardId));
    } catch (err) {
      console.error("❌ Error deleting card:", err);
      setError("Failed to delete card. Please try again.");
    }
  };

  const handleCheckEbayPrice = async (cardId) => {
    setEbayDialog({
      open: true,
      loading: true,
      data: null,
      error: null,
      cardId: cardId,
    });

    try {
      const response = await axios.post(`http://127.0.0.1:8000/cards/${cardId}/check-ebay-price`);
      setEbayDialog((prev) => ({
        ...prev,
        loading: false,
        data: response.data,
      }));

      // Update the card's Track Card in the table
      setCards((prevCards) =>
        prevCards.map((card) =>
          card.id === cardId
            ? { ...card, current_value: response.data.avg_sold_price }
            : card
        )
      );
    } catch (err) {
      console.error("❌ Error checking Track Card:", err);
      setEbayDialog((prev) => ({
        ...prev,
        loading: false,
        error: err.response?.data?.detail || "Failed to check Track Card. Please try again.",
      }));
    }
  };

  const handleCloseEbayDialog = () => {
    setEbayDialog({
      open: false,
      loading: false,
      data: null,
      error: null,
      cardId: null,
      showRefinementHelp: false,
    });
  };

  const handleConfirmCard = () => {
    showTemporaryAlert("success", "Card verified! Pricing data has been saved.");
    handleCloseEbayDialog();
  };

  const handleIncorrectCard = () => {
    setEbayDialog(prev => ({
      ...prev,
      showRefinementHelp: true,
    }));
  };
  const loadTrackedCards = async () => {
    try {
      const res = await axios.get("http://127.0.0.1:8000/cards/tracked/");
      const ids = new Set((res.data || []).map((card) => card.id));
      setTrackedIds(ids);
    } catch (e) {
      console.error("Failed to load tracked cards", e);
    } finally {
      setTrackingLoading(false);
    }
  };

  const handleTrackToggle = async (cardId) => {
    try {
      const nextIds = new Set(trackedIds);
      if (!nextIds.has(cardId)) {
        nextIds.add(cardId);
      }
      await axios.post("http://127.0.0.1:8000/cards/update-tracking", { card_ids: Array.from(nextIds) });
      setTrackedIds(new Set(nextIds));
      setCards((prev) => prev.map((c) => (c.id === cardId ? { ...c, tracked_for_pricing: true } : c)));
      showTemporaryAlert("success", "Card is now tracked.");
    } catch (e) {
      showTemporaryAlert("error", "Failed to update tracking. Please try again.");
    }
  };

  // Columns definition for consistent header/body alignment
  const columns = [
    { key: 'player', label: 'Player', width: '16%', align: 'left' },
    { key: 'set_name', label: 'Set Name', width: '16%', align: 'left' },
    { key: 'year', label: 'Year', width: '8%', align: 'left' },
    { key: 'card_number', label: 'Card #', width: '10%', align: 'left' },
    { key: 'variety', label: 'Variety', width: '12%', align: 'left' },
    { key: 'graded', label: 'Graded', width: '12%', align: 'left' },
    { key: 'current_value', label: 'Value', width: '12%', align: 'right' },
    { key: 'actions', label: 'Actions', width: '14%', align: 'center' },
  ];

  if (error) {
    return (
      <VuiBox mb={3}>
        <VuiAlert color="error">{error}</VuiAlert>
      </VuiBox>
    );
  }


  return (
    <VuiBox>
      {/* Filters */}
      <VuiBox
        mb={3}
        sx={{
          background: 'linear-gradient(127.09deg, rgba(6, 11, 40, 0.94) 19.41%, rgba(10, 14, 35, 0.49) 76.65%)',
          borderRadius: '15px',
          padding: '20px',
          boxShadow: '0px 3.5px 5.5px rgba(0, 0, 0, 0.02)',
        }}
      >
        <VuiTypography variant="h5" color="white" fontWeight="bold" mb={2}>
          Filter Cards
        </VuiTypography>
        <Grid container spacing={2}>
          <Grid item xs={12} md={3}>
            <VuiInput
              name="set_name"
              placeholder="Set Name"
              value={filters.set_name}
              onChange={handleFilterChange}
              fullWidth
            />
          </Grid>
          <Grid item xs={12} md={3}>
            <VuiInput
              name="player"
              placeholder="Player Name"
              value={filters.player}
              onChange={handleFilterChange}
              fullWidth
            />
          </Grid>
          <Grid item xs={12} md={3}>
            <VuiInput
              name="year"
              placeholder="Year"
              value={filters.year}
              onChange={handleFilterChange}
              fullWidth
            />
          </Grid>
          <Grid item xs={12} md={3} display="flex" gap={1}>
            <VuiButton color="info" onClick={handleSearch} fullWidth>
              Search
            </VuiButton>
            <VuiButton color="secondary" onClick={handleClearFilters} fullWidth>
              Clear
            </VuiButton>
          </Grid>
        </Grid>
      </VuiBox>

      {/* Statistics */}
      <VuiBox mb={3}>
        <VuiBox
          sx={{
            background: 'linear-gradient(127.09deg, rgba(6, 11, 40, 0.94) 19.41%, rgba(10, 14, 35, 0.49) 76.65%)',
            borderRadius: '15px',
            padding: '20px',
            boxShadow: '0px 3.5px 5.5px rgba(0, 0, 0, 0.02)',
          }}
        >
          <VuiTypography variant="caption" color="text" textTransform="uppercase">
            Total Cards in Collection
          </VuiTypography>
          <VuiTypography variant="h2" color="white" fontWeight="bold">
            {cards.length}
          </VuiTypography>
        </VuiBox>
      </VuiBox>

      {/* Cards Table */}
      <VuiBox
        sx={{
          background: 'linear-gradient(127.09deg, rgba(6, 11, 40, 0.94) 19.41%, rgba(10, 14, 35, 0.49) 76.65%)',
          borderRadius: '15px',
          padding: '20px',
          boxShadow: '0px 3.5px 5.5px rgba(0, 0, 0, 0.02)',
        }}
      >
        {/* CSS Grid header */}
        <VuiBox sx={{ display: 'grid', gridTemplateColumns: '16% 16% 8% 10% 12% 12% 12% 14%', alignItems: 'center', px: 2, py: 1.5, borderBottom: '1px solid rgba(226, 232, 240, 0.1)' }}>
          {columns.map((c) => (
            <VuiTypography
              key={c.key}
              variant="caption"
              color="white"
              sx={{
                textTransform: 'uppercase',
                fontWeight: 'bold',
                fontSize: '12px',
                textAlign: c.align === 'right' ? 'right' : c.align === 'center' ? 'center' : 'left',
              }}
            >
              {c.label}
            </VuiTypography>
          ))}
        </VuiBox>
        {/* CSS Grid body */}
        {loading || trackingLoading ? (
          <VuiBox>
            {Array.from({ length: 4 }).map((_, idx) => (
              <VuiBox
                key={`grid-skeleton-${idx}`}
              sx={{ display: 'grid', gridTemplateColumns: '16% 16% 8% 10% 12% 12% 12% 14%', alignItems: 'center', py: 1.5, borderBottom: '1px solid rgba(226, 232, 240, 0.05)' }}>
                {columns.map((col) => (
                  <Skeleton
                    key={`${idx}-${col.key}`}
                    variant="rectangular"
                    height={18}
                    animation="pulse"
                    sx={{ bgcolor: 'rgba(255, 255, 255, 0.05)', borderRadius: '6px' }}
                  />
                ))}
              </VuiBox>
            ))}
          </VuiBox>
        ) : cards.length === 0 ? (
          <VuiBox sx={{ textAlign: 'center', py: 3 }}>
            <VuiTypography variant="body2" color="text">
              No cards found. Add cards to start building your collection!
            </VuiTypography>
          </VuiBox>
        ) : (
          cards.map((card) => (
            <VuiBox
              key={card.id}
              sx={{
                display: 'grid',
                gridTemplateColumns: '16% 16% 8% 10% 12% 12% 12% 14%',
                alignItems: 'center',
                py: 1.5,
                borderBottom: '1px solid rgba(226, 232, 240, 0.1)',
                background: trackedIds.has(card.id) || card.tracked_for_pricing ? 'rgba(0, 117, 255, 0.08)' : 'transparent',
                boxShadow: trackedIds.has(card.id) || card.tracked_for_pricing ? '0px 0px 12px rgba(0, 117, 255, 0.25)' : 'none',
                transition: 'background 0.2s ease',
              }}
            >
              <VuiTypography variant="button" color="white" fontWeight="medium">
                {card.player || '-'}
                {(trackedIds.has(card.id) || card.tracked_for_pricing) && (
                  <VuiTypography component="span" variant="caption" color="success" ml={1}>
                    Tracked
                  </VuiTypography>
                )}
              </VuiTypography>
              <VuiTypography variant="button" color="text" sx={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{card.set_name || '-'}</VuiTypography>
              <VuiTypography variant="button" color="text">{card.year || '-'}</VuiTypography>
              <VuiBox>
                <VuiTypography variant="button" color="text">{card.card_number || '-'}</VuiTypography>
                {card.numbered && (<VuiTypography variant="caption" color="info" display="block">#{card.numbered}</VuiTypography>)}
              </VuiBox>
              <VuiBox>
                <VuiTypography variant="caption" color="text" sx={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{card.variety || '-'}</VuiTypography>
                {card.parallel && (<VuiTypography variant="caption" color="warning" display="block">{card.parallel}</VuiTypography>)}
              </VuiBox>
              <VuiTypography variant="button" color={card.graded ? 'success' : 'text'}>{card.graded || '-'}</VuiTypography>
              <VuiTypography variant="button" color="white" fontWeight="medium" sx={{ textAlign: 'right' }}>{card.current_value ? `$${card.current_value.toFixed(2)}` : '-'}</VuiTypography>
              <VuiBox sx={{ display: 'flex', gap: 1, justifyContent: 'center', flexWrap: 'wrap' }}>
                <VuiButton
                  color={trackedIds.has(card.id) || card.tracked_for_pricing ? 'success' : 'info'}
                  size="small"
                  disabled={trackedIds.has(card.id) || card.tracked_for_pricing}
                  onClick={() => handleTrackToggle(card.id)}
                  sx={{ minWidth: '110px' }}
                >
                  {trackedIds.has(card.id) || card.tracked_for_pricing ? 'Tracked' : 'Track Card'}
                </VuiButton>
                <VuiButton color="error" size="small" onClick={() => handleDeleteCard(card.id)} sx={{ minWidth: '60px' }}>
                  Delete
                </VuiButton>
              </VuiBox>
            </VuiBox>
          ))
        )}
      </VuiBox>

      {/* Track Card Check Dialog */}
      <Dialog
        open={ebayDialog.open}
        onClose={handleCloseEbayDialog}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            background: 'linear-gradient(127.09deg, rgba(6, 11, 40, 0.94) 19.41%, rgba(10, 14, 35, 0.49) 76.65%)',
            borderRadius: '15px',
            padding: '20px',
            boxShadow: '0px 3.5px 5.5px rgba(0, 0, 0, 0.02)',
          },
        }}
      >
        <DialogTitle>
          <VuiTypography variant="h4" color="white" fontWeight="bold">
            Track Card Check
          </VuiTypography>
        </DialogTitle>
        <DialogContent>
          {ebayDialog.loading ? (
            <VuiBox display="flex" justifyContent="center" alignItems="center" minHeight="200px">
              <CircularProgress sx={{ color: "#0075ff" }} size={40} />
              <VuiTypography variant="body2" color="text" ml={2}>
                Checking Track Cards...
              </VuiTypography>
            </VuiBox>
          ) : ebayDialog.error ? (
            <VuiAlert color="error">{ebayDialog.error}</VuiAlert>
          ) : ebayDialog.data ? (
            <VuiBox>
              {/* Enhanced Search Query Display */}
              <VuiBox
                mb={3}
                sx={{
                  background: 'rgba(255, 255, 255, 0.05)',
                  borderRadius: '10px',
                  padding: '15px',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                }}
              >
                <VuiTypography variant="caption" color="text" textTransform="uppercase" mb={1} display="block">
                  eBay Search Parameters
                </VuiTypography>
                <VuiTypography variant="h6" color="white" mb={1} fontWeight="bold">
                  {ebayDialog.data.search_keywords}
                </VuiTypography>
                <VuiBox display="flex" alignItems="center" gap={1} mt={1}>
                  <VuiTypography variant="caption" color={ebayDialog.data.listing_count > 0 ? "success" : "error"} fontWeight="bold">
                    {ebayDialog.data.listing_count > 0 ? "✓" : "✗"} {ebayDialog.data.listing_count} active listings found
                  </VuiTypography>
                </VuiBox>
                <VuiBox mt={1}>
                  <VuiTypography variant="caption" color="text" fontStyle="italic">
                    💡 Search includes: Year, Set, Player, Card #, and all variants (parallel, graded, autograph)
                  </VuiTypography>
                </VuiBox>
              </VuiBox>

              {ebayDialog.data.avg_sold_price && (
                <VuiBox
                  mb={3}
                  sx={{
                    background: 'rgba(0, 117, 255, 0.1)',
                    borderRadius: '10px',
                    padding: '20px',
                    border: '1px solid rgba(0, 117, 255, 0.3)',
                  }}
                >
                  <VuiTypography variant="caption" color="text" textTransform="uppercase" mb={1}>
                    Pricing Statistics
                  </VuiTypography>
                  <VuiBox display="flex" justifyContent="space-between" mb={1}>
                    <VuiTypography variant="body2" color="text">
                      Average Price:
                    </VuiTypography>
                    <VuiTypography variant="h5" color="success" fontWeight="bold">
                      ${ebayDialog.data.avg_sold_price?.toFixed(2) || 'N/A'}
                    </VuiTypography>
                  </VuiBox>
                  <VuiBox display="flex" justifyContent="space-between" mb={1}>
                    <VuiTypography variant="caption" color="text">
                      Min Price:
                    </VuiTypography>
                    <VuiTypography variant="caption" color="white">
                      ${ebayDialog.data.min_price?.toFixed(2) || 'N/A'}
                    </VuiTypography>
                  </VuiBox>
                  <VuiBox display="flex" justifyContent="space-between">
                    <VuiTypography variant="caption" color="text">
                      Max Price:
                    </VuiTypography>
                    <VuiTypography variant="caption" color="white">
                      ${ebayDialog.data.max_price?.toFixed(2) || 'N/A'}
                    </VuiTypography>
                  </VuiBox>
                </VuiBox>
              )}

              {/* Sample Card Images for Visual Verification */}
              {ebayDialog.data.sample_images && ebayDialog.data.sample_images.length > 0 && (
                <VuiBox mb={3}>
                  <VuiTypography variant="h6" color="white" mb={2} fontWeight="bold">
                    These are the listings we're using for pricing:
                  </VuiTypography>
                  <VuiBox display="flex" gap={2} flexWrap="wrap" justifyContent="center">
                    {ebayDialog.data.sample_images.map((imageUrl, index) => (
                      <VuiBox
                        key={index}
                        component="a"
                        href={ebayDialog.data.sample_urls?.[index] || '#'}
                        target="_blank"
                        rel="noopener noreferrer"
                        sx={{
                          border: '2px solid rgba(0, 117, 255, 0.3)',
                          borderRadius: '10px',
                          padding: '10px',
                          background: 'rgba(0, 117, 255, 0.05)',
                          flex: '0 1 auto',
                          maxWidth: '200px',
                          cursor: 'pointer',
                          textDecoration: 'none',
                          transition: 'all 0.2s ease',
                          '&:hover': {
                            border: '2px solid rgba(0, 117, 255, 0.6)',
                            background: 'rgba(0, 117, 255, 0.15)',
                            transform: 'scale(1.05)',
                          },
                        }}
                      >
                        <img
                          src={imageUrl}
                          alt={`Card listing ${index + 1}`}
                          style={{
                            width: '100%',
                            height: 'auto',
                            borderRadius: '5px',
                            display: 'block',
                          }}
                        />
                        <VuiTypography variant="caption" color="info" textAlign="center" display="block" mt={1}>
                          Click to view listing
                        </VuiTypography>
                      </VuiBox>
                    ))}
                  </VuiBox>
                  {!ebayDialog.showRefinementHelp && (
                    <VuiBox mt={2}>
                      <VuiAlert color="info">
                        Click on an image to view the full eBay listing. Verify these match your card.
                      </VuiAlert>
                    </VuiBox>
                  )}
                  {ebayDialog.showRefinementHelp && (
                    <VuiBox mt={2}>
                      <VuiAlert color="warning">
                        These listings don't match your card? You may need to update your card details to refine the search.
                        <br /><br />
                        <strong>Suggestions:</strong>
                        <ul style={{ marginTop: '8px', marginBottom: 0, paddingLeft: '20px' }}>
                          <li>Verify the card number is correct</li>
                          <li>Check if parallel/variety information is accurate</li>
                          <li>Ensure grading status (PSA, BGS, etc.) is specified if applicable</li>
                          <li>Confirm autograph status is marked correctly</li>
                        </ul>
                        <br />
                        Close this dialog and edit the card details in the main table, then try the price check again.
                      </VuiAlert>
                    </VuiBox>
                  )}
                </VuiBox>
              )}


              {(!ebayDialog.data.avg_sold_price || ebayDialog.data.listing_count === 0) && (
                <VuiAlert color="warning">
                  No pricing data available for this card. Try checking the search query or try again later.
                </VuiAlert>
              )}
            </VuiBox>
          ) : null}
        </DialogContent>
        <DialogActions sx={{ padding: '20px', gap: 2 }}>
          {!ebayDialog.showRefinementHelp ? (
            <>
              <VuiButton
                color="error"
                variant="outlined"
                onClick={handleIncorrectCard}
                sx={{ flex: 1 }}
              >
                This is NOT the Right Card
              </VuiButton>
              <VuiButton
                color="success"
                onClick={handleConfirmCard}
                sx={{ flex: 1 }}
              >
                This is Correct - Confirm
              </VuiButton>
            </>
          ) : (
            <VuiButton
              color="secondary"
              onClick={handleCloseEbayDialog}
              fullWidth
            >
              Close
            </VuiButton>
          )}
        </DialogActions>
      </Dialog>
    </VuiBox>
  );
}



