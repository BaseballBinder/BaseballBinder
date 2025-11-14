import React, { useEffect, useState, useMemo, useCallback, useRef } from "react";
import axios from "axios";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TableContainer,
  Skeleton,
  Tooltip,
  Chip,
  Switch,
  FormControlLabel,
} from "@mui/material";
import VuiBox from "components/VuiBox";
import VuiTypography from "components/VuiTypography";
import VuiAlert from "components/VuiAlert";
import VuiButton from "components/VuiButton";
import VuiInput from "components/VuiInput";
import { Grid } from "@mui/material";

const API_BASE = process.env.REACT_APP_BACKEND_URL || "http://127.0.0.1:8000";

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
  const initialMatchDialogState = {
    open: false,
    loading: false,
    card: null,
    items: [],
    searchHistoryId: null,
    selectedItemId: "",
    intent: null,
    showHelp: false,
    error: null,
    searchQuery: "",
    strategy: "strict",
    strategies: [],
    strategyQueries: {},
    filters: null,
    context: null,
    infoMessage: "",
    rejectedCount: 0,
    rejectedSamples: [],
    previewLocked: false,
    manuallyEdited: false,
    optionsLoaded: false,
  };
  const [matchDialog, setMatchDialog] = useState(initialMatchDialogState);
  const [trackingActionId, setTrackingActionId] = useState(null);
  const [sortConfig, setSortConfig] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("collectionSortConfig")) || { key: "player", direction: "asc" };
    } catch {
      return { key: "player", direction: "asc" };
    }
  });
  const [previewBatch, setPreviewBatch] = useState({ running: false, total: 0, completed: 0 });
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editCard, setEditCard] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [editSaving, setEditSaving] = useState(false);
  const [editError, setEditError] = useState(null);
  const [searchPreferences, setSearchPreferences] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("cardImageSearchPrefs")) || {};
    } catch {
      return {};
    }
  });
  const searchCooldownRef = useRef(null);
  const [searchCoolingDown, setSearchCoolingDown] = useState(false);

  const editFieldConfig = [
    {
      name: "player",
      label: "Player Name",
      helper: "Exact name as printed on the card so we can search accurately.",
      placeholder: "e.g., Derek Jeter",
      grid: { xs: 12, md: 6 },
    },
    {
      name: "set_name",
      label: "Set Name",
      helper: "Product/series name (Topps Chrome, Donruss Optic, etc.).",
      placeholder: "e.g., Topps Chrome",
      grid: { xs: 12, md: 6 },
    },
    {
      name: "year",
      label: "Release Year",
      helper: "Year printed on the checklist/card back.",
      placeholder: "e.g., 2022",
      grid: { xs: 12, md: 4 },
    },
    {
      name: "card_number",
      label: "Card Number",
      helper: "Card # from the checklist (helps match exact listing).",
      placeholder: "e.g., HOC-13",
      grid: { xs: 12, md: 4 },
    },
    {
      name: "team",
      label: "Team",
      helper: "Team name on the card (used in fallback searches).",
      placeholder: "e.g., New York Yankees",
      grid: { xs: 12, md: 4 },
    },
    {
      name: "variety",
      label: "Insert / Subset",
      helper: "Insert name or subset (Heart of the City, Rated Rookie, etc.).",
      placeholder: "e.g., Heart of the City",
      grid: { xs: 12, md: 6 },
    },
    {
      name: "parallel",
      label: "Parallel / Finish",
      helper: "Color/finish variation (Refractor, Gold /50, etc.).",
      placeholder: "e.g., Refractor",
      grid: { xs: 12, md: 6 },
    },
    {
      name: "numbered",
      label: "Serial Numbering",
      helper: "Enter the print run if numbered (format: /99, /5, etc.).",
      placeholder: "e.g., /99",
      grid: { xs: 12, md: 6 },
    },
    {
      name: "graded",
      label: "Grading",
      helper: "If graded, include company and grade (PSA 10, BGS 9.5, etc.).",
      placeholder: "e.g., PSA 10",
      grid: { xs: 12, md: 6 },
    },
    {
      name: "notes",
      label: "Collector Notes",
      helper: "Private notes or reminders for this card.",
      placeholder: "e.g., Pulled at show, check for surface scratch.",
      grid: { xs: 12, md: 12 },
      multiline: true,
      minRows: 3,
    },
  ];

  const showTemporaryAlert = (type, message, duration = 3000) => {
    setAlert({ show: true, type, message });
    if (duration) {
      setTimeout(() => {
        setAlert({ show: false, type: "", message: "" });
      }, duration);
    }
  };

  const persistSearchPreference = useCallback((cardId, payload) => {
    setSearchPreferences((prev) => {
      const next = {
        ...prev,
        [cardId]: {
          ...(prev[cardId] || {}),
          ...payload,
        },
      };
      try {
        localStorage.setItem("cardImageSearchPrefs", JSON.stringify(next));
      } catch {
        // ignore storage errors
      }
      return next;
    });
  }, []);

  const triggerSearchCooldown = useCallback(() => {
    setSearchCoolingDown(true);
    if (searchCooldownRef.current) {
      clearTimeout(searchCooldownRef.current);
    }
    searchCooldownRef.current = setTimeout(() => {
      setSearchCoolingDown(false);
    }, 500);
  }, []);

  const fetchCards = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = {};
      if (filters.set_name) params.set_name = filters.set_name;
      if (filters.player) params.player = filters.player;
      if (filters.year) params.year = filters.year;

      const res = await axios.get(`${API_BASE}/cards/`, { params });
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

  useEffect(() => {
    localStorage.setItem("collectionSortConfig", JSON.stringify(sortConfig));
  }, [sortConfig]);

  useEffect(() => {
    return () => {
      if (searchCooldownRef.current) {
        clearTimeout(searchCooldownRef.current);
      }
    };
  }, []);

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
      setEditSaving(true);
      await axios.delete(`${API_BASE}/cards/${cardId}`);
      setCards((prev) => prev.filter((card) => card.id !== cardId));
      setEditDialogOpen(false);
      setEditCard(null);
      setEditForm({});
      setEditSaving(false);
      setEditError(null);
      showTemporaryAlert("success", "Card deleted.");
    } catch (err) {
      console.error("❌ Error deleting card:", err);
      setError("Failed to delete card. Please try again.");
      setEditSaving(false);
    }
  };

  const openEditDialog = (card) => {
    if (!card) return;
    setEditDialogOpen(true);
    setEditCard(card);
    setEditForm({
      player: card.player || "",
      set_name: card.set_name || "",
      year: card.year || "",
      card_number: card.card_number || "",
      variety: card.variety || "",
      parallel: card.parallel || "",
      team: card.team || "",
      graded: card.graded || "",
      autograph: card.autograph || false,
      numbered: card.numbered || "",
      notes: card.notes || "",
    });
    setEditSaving(false);
    setEditError(null);
  };

  const closeEditDialog = () => {
    setEditDialogOpen(false);
    setEditCard(null);
    setEditForm({});
    setEditSaving(false);
    setEditError(null);
  };

  const handleEditFieldChange = (e) => {
    const { name, value, type, checked } = e.target;
    setEditForm((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleSaveEdit = async () => {
    if (!editCard) return;
    try {
      setEditSaving(true);
      setEditError(null);
      await axios.put(`${API_BASE}/cards/${editCard.id}`, editForm);
      await fetchCards();
      showTemporaryAlert("success", "Card details updated.");
      closeEditDialog();
    } catch (error) {
      console.error("Failed to update card", error);
      setEditSaving(false);
      setEditError(error.response?.data?.detail || "Failed to update card. Please try again.");
    }
  };

  const performPriceCheck = async (cardId) => {
    setEbayDialog({
      open: true,
      loading: true,
      data: null,
      error: null,
      cardId,
    });

    try {
      const response = await axios.post(`${API_BASE}/cards/${cardId}/check-ebay-price`);
      setEbayDialog((prev) => ({
        ...prev,
        loading: false,
        data: response.data,
      }));

      setCards((prevCards) =>
        prevCards.map((card) =>
          card.id === cardId ? { ...card, current_value: response.data.avg_sold_price } : card
        )
      );
    } catch (err) {
      console.error("Error checking Track Card:", err);
      setEbayDialog((prev) => ({
        ...prev,
        loading: false,
        error: err.response?.data?.detail || "Failed to check Track Card. Please try again.",
      }));
    }
  };

  const handleCheckEbayPrice = (card) => {
    if (!card) return;
    if (!card.last_price_check) {
      openMatchDialog(card, "price");
    } else {
      performPriceCheck(card.id);
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
      const res = await axios.get(`${API_BASE}/cards/tracked/`);
      const tracked = res.data || [];
      const ids = new Set(tracked.map((card) => card.id));
      const trackedMap = new Map(tracked.map((card) => [card.id, card.tracked_since]));
      setTrackedIds(ids);
      setCards((prev) =>
        prev.map((card) =>
          ids.has(card.id)
            ? { ...card, tracked_for_pricing: true, tracked_since: trackedMap.get(card.id) || card.tracked_since }
            : { ...card, tracked_for_pricing: false, tracked_since: null }
        )
      );
    } catch (e) {
      console.error("Failed to load tracked cards", e);
    } finally {
      setTrackingLoading(false);
    }
  };

  const formatNumberedTerm = (value) => {
    if (!value) return "";
    if (typeof value !== "string") value = String(value);
    const slashMatch = value.match(/\/\d+$/);
    if (slashMatch) {
      return slashMatch[0];
    }
    const digits = value.replace(/[^\d/]/g, "");
    if (digits.includes("/")) {
      const denom = digits.split("/").pop();
      return denom ? `/${denom}` : "";
    }
    return value.trim();
  };

  const generateDefaultSearchQuery = (card) => {
    if (!card) return "";
    const numberedTerm = formatNumberedTerm(card.numbered);
    const segments = [
      card.player,
      card.year,
      card.set_name,
      card.variety,
      card.parallel,
      numberedTerm,
      card.autograph ? "autograph" : "",
    ];
    return segments.filter((segment) => segment && segment.toString().trim().length > 0).join(" ").trim();
  };

  const strategySequence = ["strict", "focused", "broad"];

  const mapStrategyQueries = (strategies = []) => {
    const map = {};
    strategies.forEach((option) => {
      if (option?.key) {
        map[option.key] = (option.query || "").trim();
      }
    });
    return map;
  };

  const buildFrontendDefaultFilters = (card) => ({
    require_player: true,
    require_year: Boolean(card?.year),
    require_set: Boolean(card?.set_name),
    require_single_card: true,
    require_numbering: Boolean(formatNumberedTerm(card?.numbered)),
    require_grade: Boolean(card?.graded),
    exclude_phrases: [],
  });

  const getStrategyLabel = (strategies, key) => {
    const found = strategies?.find((opt) => opt.key === key);
    return found?.label || key;
  };

  const getStrategyOrder = (preferred) => {
    const base = preferred || "strict";
    return [base, ...strategySequence.filter((item) => item !== base)];
  };

  const getListingImageUrl = (item) =>
    item?.image?.imageUrl ||
    item?.image_url ||
    item?.imageUrl ||
    item?.previewImageUrl ||
    item?.thumbnail ||
    null;

  const getListingLinkUrl = (item) =>
    item?.itemWebUrl ||
    item?.item_url ||
    item?.itemUrl ||
    item?.viewItemURL ||
    null;

  const ensureCardPreview = async (card, preferredPreview) => {
    if (!card) {
      return null;
    }

    if (preferredPreview) {
      try {
        await axios.post(`${API_BASE}/cards/${card.id}/preview`, {
          preview_image_url: preferredPreview,
          preview_fit: 'cover',
          preview_focus: 50,
          preview_zoom: 1,
        });
        setCards((prev) =>
        prev.map((c) =>
          c.id === card.id
            ? { ...c, preview_image_url: preferredPreview, preview_fit: 'cover', preview_focus: 50, preview_zoom: 1 }
            : c
        )
        );
      } catch (error) {
        console.error("Failed to persist preview image", error);
      }
      return preferredPreview;
    }

    if (card.preview_image_url) {
      return card.preview_image_url;
    }

    try {
      const queryString = generateDefaultSearchQuery(card);
      const url = queryString
        ? `${API_BASE}/cards/${card.id}/search-with-images?q=${encodeURIComponent(queryString)}`
        : `${API_BASE}/cards/${card.id}/search-with-images`;
      const res = await axios.get(url);
      const preview =
        res.data?.sample_images?.[0] ||
        getListingImageUrl(res.data?.items?.[0]) ||
        null;

      if (preview) {
        await axios.post(`${API_BASE}/cards/${card.id}/preview`, {
          preview_image_url: preview,
          preview_fit: 'cover',
          preview_focus: 50,
          preview_zoom: 1,
        });
      }

      setCards((prev) =>
        prev.map((c) =>
          c.id === card.id
            ? { ...c, preview_image_url: preview, preview_fit: 'cover', preview_focus: 50, preview_zoom: 1 }
            : c
        )
      );

      return preview;
    } catch (error) {
      console.error("Failed to fetch preview image", error);
      return null;
    }
  };
  const fetchMatchListings = async (
    cardArg,
    intentOverride,
    queryOverride,
    strategyOverride,
    filtersOverride,
    strategyQueriesOverride,
    options = {}
  ) => {
    const targetCard = cardArg || matchDialog.card;
    if (!targetCard) {
      setMatchDialog((prev) => ({
        ...prev,
        loading: false,
        error: "We lost track of which card you were editing. Close and reopen the dialog to try again.",
      }));
      return;
    }

    const filters =
      filtersOverride ||
      matchDialog.filters ||
      buildFrontendDefaultFilters(targetCard);
    const strategyQueries = strategyQueriesOverride || matchDialog.strategyQueries || {};
    const strategyList = options.strategyList || matchDialog.strategies || [];
    const manualQuery = (queryOverride ?? matchDialog.searchQuery ?? "").trim();
    const manualOverride = options.manualOverride ?? matchDialog.manuallyEdited;
    const preferredStrategy = strategyOverride || matchDialog.strategy || "strict";
    const order = options.allowFallback === false ? [preferredStrategy] : getStrategyOrder(preferredStrategy);

    let finalData = null;
    let lastError = null;
    let finalStrategy = preferredStrategy;
    let finalQueryUsed = manualQuery;
    let finalHistoryId = null;

    setMatchDialog((prev) => ({
      ...prev,
      card: targetCard,
      intent: intentOverride || prev.intent || "price",
      loading: true,
      error: null,
      infoMessage: "",
    }));

    for (const strategyKey of order) {
      const queryForStrategy = manualOverride
        ? manualQuery
        : (strategyQueries[strategyKey] || manualQuery || generateDefaultSearchQuery(targetCard)).trim();

      if (!queryForStrategy) {
        lastError = "Unable to build a search query for this card.";
        continue;
      }

      try {
        const res = await axios.post(`${API_BASE}/cards/${targetCard.id}/image-search`, {
          query: queryForStrategy,
          strategy: strategyKey,
          filters,
          limit: options.limit || 24,
          record_history: options.recordHistory !== false,
        });

        const items = res.data?.items || [];
        if (items.length > 0) {
          finalData = res.data;
          finalStrategy = strategyKey;
          finalQueryUsed = queryForStrategy;
          finalHistoryId = res.data?.search_history_id || null;
          break;
        }

        lastError =
          res.data?.message ||
          `No matches for the ${getStrategyLabel(strategyList, strategyKey)} search.`;
      } catch (error) {
        lastError =
          error.response?.data?.detail ||
          "Failed to load eBay listings. Please refine the card details and try again.";
      }
    }

    setMatchDialog((prev) => ({
      ...prev,
      loading: false,
      items: finalData?.items || [],
      searchHistoryId: finalData?.items?.length ? finalHistoryId : null,
      selectedItemId: finalData?.items?.[0]?.item_id || "",
      showHelp: !finalData?.items?.length,
      error: finalData?.items?.length ? null : lastError || "No listings found even after trying broader searches.",
      searchQuery: finalQueryUsed,
      strategy: finalStrategy,
      filters,
      strategyQueries: Object.keys(strategyQueries).length ? strategyQueries : prev.strategyQueries,
      rejectedCount: finalData?.rejected_count || 0,
      rejectedSamples: finalData?.rejected_samples || [],
      infoMessage:
        finalData?.rejected_count && finalData.rejected_count > 0
          ? `${finalData.rejected_count} listings were filtered out automatically.`
          : "",
      context: finalData?.context || prev.context,
    }));
    if (targetCard) {
      persistSearchPreference(targetCard.id, {
        strategy: finalStrategy,
        query: finalQueryUsed,
        filters,
        manuallyEdited: manualOverride,
      });
    }
  };

  const openMatchDialog = (card, intent = "price") => {
    if (!card) return;
    setSearchCoolingDown(false);
    setMatchDialog({
      ...initialMatchDialogState,
      open: true,
      loading: true,
      card,
      intent,
    });

    (async () => {
      try {
        const res = await axios.get(`${API_BASE}/cards/${card.id}/image-search/options`);
        const strategies = res.data?.strategies || [];
        const strategyMap = mapStrategyQueries(strategies);
        const defaultStrategy = res.data?.default_strategy || strategies[0]?.key || "strict";
        const savedPref = searchPreferences[card.id] || {};
        const defaultQueryBase =
          res.data?.default_query ||
          strategyMap[defaultStrategy] ||
          generateDefaultSearchQuery(card);
        const preferredStrategy = savedPref.strategy || defaultStrategy;
        const filters = savedPref.filters || res.data?.filters || buildFrontendDefaultFilters(card);
        const defaultQuery =
          savedPref.query ||
          strategyMap[preferredStrategy] ||
          defaultQueryBase;

        setMatchDialog((prev) => ({
          ...prev,
          open: true,
          loading: true,
          card,
          intent,
          strategy: preferredStrategy,
          strategies,
          strategyQueries: strategyMap,
          filters,
          context: res.data?.context || null,
          previewLocked: Boolean(res.data?.preview_locked),
          searchQuery: defaultQuery,
          optionsLoaded: true,
          manuallyEdited: Boolean(savedPref.manuallyEdited && savedPref.query),
        }));

        await fetchMatchListings(
          card,
          intent,
          defaultQuery,
          preferredStrategy,
          filters,
          strategyMap,
          { allowFallback: true, strategyList: strategies }
        );
      } catch (error) {
        setMatchDialog((prev) => ({
          ...prev,
          loading: false,
          error: error.response?.data?.detail || "Unable to load search options. Please verify the card details.",
        }));
      }
    })();
  };

  const closeMatchDialog = () => {
    if (searchCooldownRef.current) {
      clearTimeout(searchCooldownRef.current);
    }
    setSearchCoolingDown(false);
    setMatchDialog(initialMatchDialogState);
  };

  const handleMatchQueryChange = (value) => {
    setMatchDialog((prev) => ({
      ...prev,
      searchQuery: value,
      manuallyEdited: true,
    }));
    triggerSearchCooldown();
  };

  const handleListingSelect = (itemId) => {
    setMatchDialog((prev) => ({ ...prev, selectedItemId: itemId }));
  };

  const handleStrategySelect = (key) => {
    setMatchDialog((prev) => {
      if (!prev.optionsLoaded) return prev;
      const nextQuery = prev.manuallyEdited
        ? prev.searchQuery
        : prev.strategyQueries[key] || prev.searchQuery || "";
      return {
        ...prev,
        strategy: key,
        searchQuery: nextQuery,
      };
    });
    triggerSearchCooldown();
  };

  const handleResetQuery = () => {
    setMatchDialog((prev) => {
      const defaultQuery =
        prev.strategyQueries[prev.strategy] ||
        generateDefaultSearchQuery(prev.card);
      return {
        ...prev,
        searchQuery: defaultQuery || "",
        manuallyEdited: false,
      };
    });
  };

  const handleFilterToggle = (name, value) => {
    setMatchDialog((prev) => {
      const nextFilters = {
        ...(prev.filters || buildFrontendDefaultFilters(prev.card)),
        [name]: value,
      };
      return {
        ...prev,
        filters: nextFilters,
      };
    });
    triggerSearchCooldown();
  };

  const runMatchSearch = () => {
    if (!matchDialog.card || matchDialog.loading) return;
    fetchMatchListings(
      matchDialog.card,
      matchDialog.intent,
      matchDialog.searchQuery,
      matchDialog.strategy,
      matchDialog.filters,
      matchDialog.strategyQueries,
      { allowFallback: true, manualOverride: matchDialog.manuallyEdited, strategyList: matchDialog.strategies }
    );
  };

  const toggleMatchHelp = () => {
    setMatchDialog((prev) => ({ ...prev, showHelp: !prev.showHelp }));
  };

  const confirmListingSelection = async () => {
    const { card, intent, selectedItemId, searchHistoryId } = matchDialog;
    if (!card || !selectedItemId || !searchHistoryId) {
      setMatchDialog((prev) => ({
        ...prev,
        error: "Select the listing that matches your card to continue.",
      }));
      return;
    }

    setMatchDialog((prev) => ({ ...prev, loading: true, error: null }));
    try {
      await axios.post(`${API_BASE}/cards/${card.id}/confirm-selection`, null, {
        params: {
          search_history_id: searchHistoryId,
          selected_item_id: selectedItemId,
        },
      });

      const selectedItem = matchDialog.items.find((item) => item.item_id === selectedItemId);
      const selectedPreview = getListingImageUrl(selectedItem);
      const previewUpdate = selectedPreview || card.preview_image_url || null;
      if (selectedPreview) {
        setCards((prev) =>
          prev.map((c) =>
            c.id === card.id
              ? {
                  ...c,
                  preview_image_url: previewUpdate,
                  preview_confirmed: true,
                  preview_source: "ebay-selection",
                  preview_confirmed_at: new Date().toISOString(),
                }
              : c
          )
        );
      }

      closeMatchDialog();

      if (intent === "track") {
        await finalizeTrackCard(card);
      } else if (intent === "price") {
        await performPriceCheck(card.id);
      } else if (intent === "preview") {
        showTemporaryAlert("success", "Card image updated.");
      }
    } catch (error) {
      setMatchDialog((prev) => ({
        ...prev,
        loading: false,
        error: error.response?.data?.detail || "Failed to confirm selection. Please try again.",
      }));
    }
  };

  const finalizeTrackCard = async (card) => {
    if (!card) return;

    try {
      setTrackingActionId(card.id);
      await ensureCardPreview(card);

      const nextIds = new Set(trackedIds);
      if (!nextIds.has(card.id)) {
        nextIds.add(card.id);
      }

      await axios.post(`${API_BASE}/cards/update-tracking`, { card_ids: Array.from(nextIds) });

      const trackedAt = new Date().toISOString();
      setTrackedIds(new Set(nextIds));
      setCards((prev) =>
        prev.map((c) =>
          c.id === card.id ? { ...c, tracked_for_pricing: true, tracked_since: trackedAt } : c
        )
      );
      showTemporaryAlert("success", "Card is now tracked.");
    } catch (e) {
      showTemporaryAlert("error", "Failed to update tracking. Please try again.");
    } finally {
      setTrackingActionId(null);
    }
  };

  const handleTrackToggle = (card) => {
    if (!card) return;
    if (!card.preview_image_url) {
      openMatchDialog(card, "track");
    } else {
      finalizeTrackCard(card);
    }
  };

  const handleGetPicture = (card) => {
    if (!card) return;
    openMatchDialog(card, "preview");
  };

  const handleBulkPreviewFetch = async () => {
    if (previewBatch.running) return;
    const candidates = sortedCards.filter((card) => !card.preview_image_url);
    if (!candidates.length) {
      showTemporaryAlert("info", "All visible cards already have previews.");
      return;
    }
    setPreviewBatch({ running: true, total: candidates.length, completed: 0 });
    for (let i = 0; i < candidates.length; i += 1) {
      const card = candidates[i];
      try {
        await ensureCardPreview(card);
      } catch (error) {
        console.error("Bulk preview fetch failed", error);
      } finally {
        setPreviewBatch((prev) => ({ ...prev, completed: prev.completed + 1 }));
      }
    }
    setPreviewBatch({ running: false, total: 0, completed: 0 });
    showTemporaryAlert("success", "Finished fetching previews for visible cards.");
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

  const sortableColumns = {
    player: "text",
    set_name: "text",
    year: "number",
    card_number: "text",
    variety: "text",
    graded: "text",
    current_value: "number",
  };

  const criticalFields = ["year", "set_name", "variety"];

  const getSortableValue = (card, key) => {
    if (key === "current_value") return card.current_value ?? -Infinity;
    if (key === "year") return Number(card.year) || 0;
    if (key === "card_number") return (card.card_number || "").toString().toLowerCase();
    if (key === "graded") return (card.graded || "").toString().toLowerCase();
    if (key === "variety") return (card.variety || card.parallel || "").toString().toLowerCase();
    if (key === "set_name") return (card.set_name || "").toString().toLowerCase();
    if (key === "player") return (card.player || "").toString().toLowerCase();
    return "";
  };

  const sortedCards = useMemo(() => {
    if (!sortableColumns[sortConfig.key]) return cards;
    const sorted = [...cards];
    sorted.sort((a, b) => {
      const aVal = getSortableValue(a, sortConfig.key);
      const bVal = getSortableValue(b, sortConfig.key);

      if (sortableColumns[sortConfig.key] === "number") {
        const diff = (aVal ?? 0) - (bVal ?? 0);
        return sortConfig.direction === "asc" ? diff : -diff;
      }
      const comp = aVal.localeCompare(bVal);
      return sortConfig.direction === "asc" ? comp : -comp;
    });
    return sorted;
  }, [cards, sortConfig]);

  const handleSortChange = (key) => {
    if (!sortableColumns[key]) return;
    setSortConfig((prev) => {
      if (prev.key === key) {
        return { key, direction: prev.direction === "asc" ? "desc" : "asc" };
      }
      return { key, direction: "asc" };
    });
  };

  const isCriticalMissing = (name) => criticalFields.includes(name) && (!editForm[name] || !editForm[name].toString().trim().length);
  const missingCritical = criticalFields.filter((field) => isCriticalMissing(field));

  const actionButtonSx = {
    width: '140px',
    minWidth: '140px',
    justifyContent: 'center',
  };

  if (error) {
    return (
      <VuiBox mb={3}>
        <VuiAlert color="error">{error}</VuiAlert>
      </VuiBox>
    );
  }


  const displayCards = sortedCards;
  const searchButtonDisabled = matchDialog.loading || searchCoolingDown || !matchDialog.searchQuery?.trim();
  const searchButtonLabel = matchDialog.loading ? "Searching..." : searchCoolingDown ? "Preparing..." : "Search";

  return (
    <VuiBox>
      {alert.show && (
        <VuiBox
          sx={{
            position: 'fixed',
            top: '90px',
            right: '30px',
            zIndex: 1300,
            minWidth: '280px',
          }}
        >
          <VuiAlert color={alert.type || "info"}>{alert.message}</VuiAlert>
        </VuiBox>
      )}
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

      <VuiBox mb={2} display="flex" justifyContent="flex-end" alignItems="center" gap={2}>
        {previewBatch.running && (
          <VuiTypography variant="caption" color="text">
            Fetching previews {previewBatch.completed}/{previewBatch.total}
          </VuiTypography>
        )}
        <VuiButton
          color="info"
          variant="outlined"
          onClick={handleBulkPreviewFetch}
          disabled={previewBatch.running || !sortedCards.length}
        >
          {previewBatch.running ? "Fetching..." : "Fetch Previews for Visible Cards"}
        </VuiButton>
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
          {columns.map((c) => {
            const sortable = !!sortableColumns[c.key];
            const isActive = sortConfig.key === c.key;
            const directionArrow = isActive ? (sortConfig.direction === "asc" ? "▲" : "▼") : "";
            return (
              <VuiTypography
                key={c.key}
                variant="caption"
                color="white"
                onClick={() => sortable && handleSortChange(c.key)}
                sx={{
                  textTransform: 'uppercase',
                  fontWeight: 'bold',
                  fontSize: '12px',
                  textAlign: c.align === 'right' ? 'right' : c.align === 'center' ? 'center' : 'left',
                  cursor: sortable ? 'pointer' : 'default',
                  userSelect: 'none',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  justifyContent: c.align === 'right' ? 'flex-end' : c.align === 'center' ? 'center' : 'flex-start',
                }}
              >
                {c.label} {directionArrow}
              </VuiTypography>
            );
          })}
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
        ) : displayCards.length === 0 ? (
          <VuiBox sx={{ textAlign: 'center', py: 3 }}>
            <VuiTypography variant="body2" color="text">
              No cards found. Add cards to start building your collection!
            </VuiTypography>
          </VuiBox>
        ) : (
          displayCards.map((card) => (
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
              <VuiBox display="flex" alignItems="center" gap={1}>
                <VuiTypography variant="button" color="white" fontWeight="medium">
                  {card.player || '-'}
                  {(trackedIds.has(card.id) || card.tracked_for_pricing) && (
                    <VuiTypography component="span" variant="caption" color="success" ml={1}>
                      Tracked
                    </VuiTypography>
                  )}
                </VuiTypography>
                {card.preview_image_url && (
                  <Tooltip
                    title={
                      <VuiBox p={1}>
                        <img
                          src={card.preview_image_url}
                          alt={`${card.player || "Card"} preview`}
                          style={{ maxWidth: '160px', maxHeight: '220px', borderRadius: '8px' }}
                        />
                      </VuiBox>
                    }
                    arrow
                    placement="top"
                  >
                    <VuiBox
                      component="span"
                      sx={{
                        width: '18px',
                        height: '18px',
                        borderRadius: '999px',
                        background: 'rgba(0,117,255,0.2)',
                        border: '1px solid rgba(0,117,255,0.8)',
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        cursor: 'pointer',
                        fontSize: '12px',
                        color: '#c8d8ff',
                      }}
                      title="Card preview available"
                    >
                      📷
                    </VuiBox>
              </Tooltip>
            )}
          </VuiBox>
          {card.tracked_since && (
            <VuiTypography variant="caption" color="text">
              Since {new Date(card.tracked_since).toLocaleDateString()}
            </VuiTypography>
          )}
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
                  disabled={trackedIds.has(card.id) || card.tracked_for_pricing || trackingActionId === card.id}
                  onClick={() => handleTrackToggle(card)}
                  sx={actionButtonSx}
                >
                  {trackedIds.has(card.id) || card.tracked_for_pricing
                    ? 'Tracked'
                    : trackingActionId === card.id
                      ? 'Tracking...'
                      : 'Track Card'}
                </VuiButton>
                <VuiButton
                  color="info"
                  variant="outlined"
                  size="small"
                  onClick={() => handleGetPicture(card)}
                  sx={{ ...actionButtonSx, color: 'white !important', borderColor: 'rgba(0,117,255,0.8) !important' }}
                >
                  Get Picture
                </VuiButton>
                <VuiButton
                  color="warning"
                  size="small"
                  onClick={() => handleCheckEbayPrice(card)}
                  sx={actionButtonSx}
                >
                  {card.last_price_check ? 'Update Price' : 'Check Price'}
                </VuiButton>
                <VuiButton color="secondary" size="small" onClick={() => openEditDialog(card)} sx={actionButtonSx}>
                  Edit
                </VuiButton>
              </VuiBox>
            </VuiBox>
          ))
        )}
      </VuiBox>

      {/* Listing Confirmation Dialog */}
      <Dialog
        open={matchDialog.open}
        onClose={closeMatchDialog}
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
            Confirm eBay Listing
          </VuiTypography>
          <VuiTypography variant="body2" color="text">
            Pick the listing that matches your card so we can track the correct item.
          </VuiTypography>
        </DialogTitle>
        <DialogContent dividers sx={{ borderColor: 'rgba(255,255,255,0.05)' }}>
          {matchDialog.loading ? (
            <VuiBox display="flex" justifyContent="center" alignItems="center" py={4}>
              <CircularProgress sx={{ color: "#0075ff" }} />
            </VuiBox>
          ) : (
            <>
              {matchDialog.previewLocked && (
                <VuiBox mb={2}>
                  <VuiAlert color="info">
                    This card already has a confirmed photo. Selecting a new listing will replace the existing thumbnail.
                  </VuiAlert>
                </VuiBox>
              )}
              {matchDialog.error && (
                <VuiBox mb={2}>
                  <VuiAlert color="warning">{matchDialog.error}</VuiAlert>
                </VuiBox>
              )}
              {matchDialog.infoMessage && !matchDialog.error && (
                <VuiBox mb={2}>
                  <VuiAlert color="info">{matchDialog.infoMessage}</VuiAlert>
                </VuiBox>
              )}

              <VuiBox mb={3}>
                <VuiTypography variant="caption" color="text" mb={1} display="block" sx={{ textTransform: 'uppercase' }}>
                  Search Strategy
                </VuiTypography>
                <VuiBox display="flex" flexWrap="wrap" gap={1}>
                  {(matchDialog.strategies.length ? matchDialog.strategies : strategySequence.map((key) => ({ key, label: key }))).map((option) => {
                    const active = matchDialog.strategy === option.key;
                    return (
                      <Chip
                        key={option.key}
                        label={option.label || option.key}
                        onClick={() => handleStrategySelect(option.key)}
                        color={active ? "primary" : "default"}
                        variant={active ? "filled" : "outlined"}
                        disabled={matchDialog.loading || !matchDialog.optionsLoaded}
                        sx={{
                          borderRadius: '10px',
                          fontWeight: active ? 700 : 500,
                          background: active ? 'rgba(0,117,255,0.2)' : 'rgba(255,255,255,0.04)',
                          borderColor: active ? '#0075ff' : 'rgba(255,255,255,0.2)',
                          color: active ? '#fff' : '#a0aec0',
                        }}
                      />
                    );
                  })}
                </VuiBox>
              </VuiBox>

              <VuiBox mb={3}>
                <VuiTypography variant="caption" color="text" mb={1} display="block" sx={{ textTransform: 'uppercase' }}>
                  Search Query
                </VuiTypography>
                <VuiBox display="flex" gap={1} flexWrap="wrap">
                  <VuiInput
                    placeholder="e.g. 2022 Topps Chrome Heart of the City Aaron Judge /99 PSA 10"
                    value={matchDialog.searchQuery}
                    onChange={(e) => handleMatchQueryChange(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && matchDialog.searchQuery?.trim() && !matchDialog.loading) {
                        e.preventDefault();
                        runMatchSearch();
                      }
                    }}
                    fullWidth
                  />
                  <VuiButton
                    color="info"
                    disabled={searchButtonDisabled}
                    onClick={runMatchSearch}
                  >
                    {searchButtonLabel}
                  </VuiButton>
                  <VuiButton
                    variant="outlined"
                    color="secondary"
                    disabled={matchDialog.loading || !matchDialog.optionsLoaded}
                    onClick={handleResetQuery}
                  >
                    Reset Query
                  </VuiButton>
                </VuiBox>
              </VuiBox>

              {matchDialog.filters && (
                <VuiBox mb={3}>
                  <VuiTypography variant="caption" color="text" mb={1} display="block" sx={{ textTransform: 'uppercase' }}>
                    Filters
                  </VuiTypography>
                  <VuiBox display="flex" flexWrap="wrap" gap={2}>
                    {[
                      { key: "require_player", label: "Player must match" },
                      { key: "require_year", label: "Include year" },
                      { key: "require_set", label: "Include set/brand" },
                      { key: "require_single_card", label: "Single-card listings only" },
                      {
                        key: "require_numbering",
                        label: matchDialog.context?.numbered_term
                          ? `Mention numbering (${matchDialog.context.numbered_term})`
                          : "Mention numbering",
                        hide: !matchDialog.context?.numbered_term,
                      },
                      {
                        key: "require_grade",
                        label: "Mention grade",
                        hide: !matchDialog.filters?.require_grade && !matchDialog.context?.grade_terms?.length,
                      },
                    ]
                      .filter((cfg) => !cfg.hide)
                      .map((cfg) => (
                        <FormControlLabel
                          key={cfg.key}
                          control={
                            <Switch
                              color="info"
                              checked={Boolean(matchDialog.filters?.[cfg.key])}
                              onChange={(e) => handleFilterToggle(cfg.key, e.target.checked)}
                              disabled={matchDialog.loading}
                            />
                          }
                          label={
                            <VuiTypography variant="body2" color="white">
                              {cfg.label}
                            </VuiTypography>
                          }
                        />
                      ))}
                  </VuiBox>
                  <VuiTypography variant="caption" color="text" mt={1}>
                    Adjust filters, then click Search to refresh the listings.
                  </VuiTypography>
                </VuiBox>
              )}

              {matchDialog.rejectedCount > 0 && (
                <VuiBox mb={2}>
                  <VuiAlert color="info">
                    {matchDialog.rejectedCount} listings were filtered out automatically. Try loosening filters if you need to see more options.
                  </VuiAlert>
                </VuiBox>
              )}

              {matchDialog.items.length > 0 ? (
                <>
                  <VuiBox mb={2} p={2} sx={{ background: 'rgba(0, 117, 255, 0.08)', borderRadius: '8px', border: '1px solid rgba(0, 117, 255, 0.3)' }}>
                    <VuiTypography variant="button" color="info" fontWeight="bold" mb={0.5}>
                      💡 How to Select a Card
                    </VuiTypography>
                    <VuiTypography variant="caption" color="text">
                      Click anywhere on a card box to select it for pricing (blue border = selected). Use "View Listing" to open eBay in a new tab.
                    </VuiTypography>
                  </VuiBox>
                  <VuiBox
                    sx={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))',
                      gap: 2,
                    }}
                  >
                  {matchDialog.items.map((item) => {
                    const isSelected = matchDialog.selectedItemId === item.item_id;
                    const imageUrl = getListingImageUrl(item);
                    const listingHref = getListingLinkUrl(item);
                    const confidence = item.confidence || "unknown";
                    const confidenceColor =
                      confidence === "high"
                        ? "#01b574"
                        : confidence === "medium"
                        ? "#fbcf33"
                        : confidence === "low"
                        ? "#e31a1a"
                        : "#a0aec0";
                    return (
                      <VuiBox
                        key={item.item_id}
                        onClick={() => handleListingSelect(item.item_id)}
                        sx={{
                          position: 'relative',
                          border: isSelected ? '3px solid #0075ff' : '1px solid rgba(255, 255, 255, 0.1)',
                          borderRadius: '12px',
                          padding: '12px',
                          background: isSelected ? 'rgba(0, 117, 255, 0.2)' : 'rgba(255, 255, 255, 0.02)',
                          cursor: 'pointer',
                          transition: 'all 0.2s ease',
                          '&:hover': {
                            borderColor: isSelected ? '#0075ff' : 'rgba(0, 117, 255, 0.5)',
                            background: isSelected ? 'rgba(0, 117, 255, 0.2)' : 'rgba(0, 117, 255, 0.08)',
                            transform: 'translateY(-2px)',
                            boxShadow: isSelected ? '0 8px 20px rgba(0, 117, 255, 0.4)' : '0 4px 12px rgba(0, 117, 255, 0.2)',
                          },
                          boxShadow: isSelected ? '0 4px 16px rgba(0, 117, 255, 0.3)' : 'none',
                        }}
                      >
                        {isSelected && (
                          <VuiBox
                            sx={{
                              position: 'absolute',
                              top: '-10px',
                              right: '10px',
                              background: '#0075ff',
                              color: 'white',
                              padding: '4px 12px',
                              borderRadius: '12px',
                              fontSize: '11px',
                              fontWeight: 'bold',
                              zIndex: 10,
                              boxShadow: '0 2px 8px rgba(0, 117, 255, 0.5)',
                            }}
                          >
                            ✓ SELECTED
                          </VuiBox>
                        )}
                        {imageUrl ? (
                          <VuiBox
                            component="img"
                            src={imageUrl}
                            alt={item.title}
                            sx={{
                              width: '100%',
                              height: '160px',
                              objectFit: 'cover',
                              borderRadius: '8px',
                              marginBottom: '12px',
                            }}
                          />
                        ) : (
                          <VuiBox
                            sx={{
                              width: '100%',
                              height: '160px',
                              borderRadius: '8px',
                              border: '1px dashed rgba(255,255,255,0.3)',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              color: '#a0aec0',
                              marginBottom: '12px',
                            }}
                          >
                            No preview
                          </VuiBox>
                        )}
                        <VuiTypography variant="caption" fontWeight="bold" sx={{ color: confidenceColor }}>
                          {confidence !== "unknown" ? `${confidence.toUpperCase()} • Score ${Math.round(item.match_score ?? 0)}` : `Score ${Math.round(item.match_score ?? 0)}`}
                        </VuiTypography>
                        {item.matched_terms?.length > 0 && (
                          <VuiTypography variant="caption" color="text" display="block">
                            Matched: {item.matched_terms.join(", ")}
                          </VuiTypography>
                        )}
                        <VuiTypography variant="button" color="white" fontWeight="medium" mt={1} mb={0.5}>
                          {item.price ? `$${Number(item.price).toFixed(2)}` : 'Price N/A'}
                        </VuiTypography>
                        <VuiTypography variant="caption" color="text">
                          {item.title}
                        </VuiTypography>
                        {listingHref && (
                          <VuiButton
                            variant="text"
                            color="info"
                            size="small"
                            sx={{ mt: 1 }}
                            onClick={(event) => {
                              event.stopPropagation();
                              window.open(listingHref, "_blank", "noopener,noreferrer");
                            }}
                          >
                            View Listing
                          </VuiButton>
                        )}
                      </VuiBox>
                    );
                  })}
                  </VuiBox>
                </>
              ) : (
                <VuiAlert color="warning">
                  {matchDialog.error ||
                    "No matching listings were found. Consider relaxing the filters or editing the card details (player, set, variety) and try again."}
                </VuiAlert>
              )}

              {matchDialog.showHelp && (
                <VuiBox mt={3}>
                  <VuiAlert color="warning">
                    These listings don&apos;t look right? Double-check the card number, insert/variety, grading, and numbering. Updating those card fields gives the search more to work with.
                  </VuiAlert>
                </VuiBox>
              )}
            </>
          )}
        </DialogContent>
        <DialogActions sx={{ padding: '20px', gap: 1, borderTop: '1px solid rgba(255,255,255,0.05)' }}>
          <VuiButton variant="outlined" color="secondary" onClick={closeMatchDialog}>
            Cancel
          </VuiButton>
          <VuiButton variant="text" color="warning" onClick={toggleMatchHelp}>
            {matchDialog.showHelp ? "Hide tips" : "Listings don't match"}
          </VuiButton>
          <VuiButton
            color="info"
            onClick={confirmListingSelection}
            disabled={matchDialog.loading || !matchDialog.selectedItemId || matchDialog.items.length === 0}
          >
            Use Selected Listing
          </VuiButton>
        </DialogActions>
      </Dialog>

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
              {(() => {
                const pricingListings = (ebayDialog.data.items || []).slice(0, 3);
                const fallbackImages = ebayDialog.data.sample_images || [];
                if (pricingListings.length === 0 && fallbackImages.length === 0) return null;
                return (
                  <VuiBox mb={3}>
                    <VuiTypography variant="h6" color="white" mb={2} fontWeight="bold">
                      These are the listings we're using for pricing:
                    </VuiTypography>
                    <VuiBox display="flex" gap={2} flexWrap="wrap" justifyContent="center">
                      {(pricingListings.length ? pricingListings : fallbackImages.map((imageUrl, index) => ({ imageUrl, itemWebUrl: ebayDialog.data.sample_urls?.[index] }))).map((item, index) => {
                        const imageUrl = item.imageUrl || getListingImageUrl(item) || '';
                        const href = getListingLinkUrl(item) || item.itemWebUrl || item.item_url || ebayDialog.data.sample_urls?.[index] || null;
                        const isClickable = Boolean(href);
                        return (
                          <VuiBox
                            key={index}
                            component={isClickable ? "a" : "div"}
                            {...(isClickable
                              ? {
                                  href,
                                  target: "_blank",
                                  rel: "noopener noreferrer",
                                }
                              : {})}
                            sx={{
                              border: '2px solid rgba(0, 117, 255, 0.3)',
                              borderRadius: '10px',
                              padding: '10px',
                              background: 'rgba(0, 117, 255, 0.05)',
                              flex: '0 1 auto',
                              maxWidth: '200px',
                              cursor: isClickable ? 'pointer' : 'default',
                              textDecoration: 'none',
                              transition: 'all 0.2s ease',
                              '&:hover': isClickable
                                ? {
                                    border: '2px solid rgba(0, 117, 255, 0.6)',
                                    background: 'rgba(0, 117, 255, 0.15)',
                                    transform: 'scale(1.05)',
                                  }
                                : {},
                            }}
                          >
                            {imageUrl ? (
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
                            ) : (
                              <VuiBox
                                sx={{
                                  width: '100%',
                                  height: '140px',
                                  borderRadius: '5px',
                                  border: '1px dashed rgba(255,255,255,0.3)',
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  color: '#a0aec0',
                                  fontSize: '12px',
                                  textAlign: 'center',
                                  px: 1,
                                }}
                              >
                                No image
                              </VuiBox>
                        )}
                        <VuiTypography variant="caption" color="info" textAlign="center" display="block" mt={1}>
                          {isClickable ? "Click to view listing" : "Listing unavailable"}
                        </VuiTypography>
                        {isClickable && (
                          <VuiButton
                            variant="text"
                            color="info"
                            size="small"
                            sx={{ mt: 0.5, textTransform: 'none' }}
                            onClick={(event) => {
                              event.stopPropagation();
                              window.open(href, "_blank", "noopener,noreferrer");
                            }}
                          >
                            View Listing
                          </VuiButton>
                        )}
                      </VuiBox>
                    );
                  })}
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
                );
              })()}


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

      {/* Edit Card Dialog */}
      <Dialog
        open={editDialogOpen}
        onClose={closeEditDialog}
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
            Edit Card
          </VuiTypography>
        </DialogTitle>
        <DialogContent dividers sx={{ borderColor: 'rgba(255,255,255,0.05)' }}>
          {editError && (
            <VuiBox mb={2}>
              <VuiAlert color="warning">{editError}</VuiAlert>
            </VuiBox>
          )}
          {missingCritical.length > 0 && (
            <VuiBox mb={2}>
              <VuiAlert color="warning">
                Adding {missingCritical.join(", ")} helps us match the right eBay listings faster.
              </VuiAlert>
            </VuiBox>
          )}
          <VuiTypography variant="body2" color="text" mb={3}>
            Update the card details below. We use this info to grab the right eBay listings, preview images, and price history for this specific card.
          </VuiTypography>
          <Grid container spacing={2}>
            {editFieldConfig.map(({ name, label, helper, placeholder, grid, multiline, minRows }) => (
              <Grid item key={name} xs={grid?.xs || 12} md={grid?.md || 6}>
                <VuiTypography variant="caption" color="text" fontWeight="bold" textTransform="uppercase">
                  {label}
                </VuiTypography>
                {helper && (
                  <VuiTypography variant="caption" color="secondary" display="block" mb={1}>
                    {helper}
                  </VuiTypography>
                )}
                <VuiBox
                  sx={{
                    border: isCriticalMissing(name) ? '1px solid rgba(227,26,26,0.6)' : '1px solid transparent',
                    borderRadius: '12px',
                    padding: '2px',
                  }}
                >
                  <VuiInput
                    name={name}
                    placeholder={placeholder}
                    value={editForm[name] ?? ""}
                    onChange={handleEditFieldChange}
                    fullWidth
                    multiline={Boolean(multiline)}
                    minRows={multiline ? minRows || 2 : undefined}
                  />
                </VuiBox>
                {isCriticalMissing(name) && (
                  <VuiTypography variant="caption" color="error">
                    Please provide {label.toLowerCase()} for better search accuracy.
                  </VuiTypography>
                )}
              </Grid>
            ))}
          </Grid>
        </DialogContent>
        <DialogActions sx={{ padding: '20px', gap: 1, borderTop: '1px solid rgba(255,255,255,0.05)' }}>
          <VuiButton variant="outlined" color="secondary" onClick={closeEditDialog} disabled={editSaving}>
            Cancel
          </VuiButton>
          <VuiButton variant="outlined" color="error" onClick={() => handleDeleteCard(editCard?.id)} disabled={editSaving}>
            Delete Card
          </VuiButton>
          <VuiButton color="info" onClick={handleSaveEdit} disabled={editSaving}>
            {editSaving ? "Saving..." : "Save Changes"}
          </VuiButton>
        </DialogActions>
      </Dialog>
    </VuiBox>
  );
}
