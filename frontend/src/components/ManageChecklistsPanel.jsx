import React, { useEffect, useMemo, useState } from "react";
import axios from "axios";
import { CircularProgress, Collapse, Modal } from "@mui/material";
import { IoChevronDown, IoChevronUp, IoRefresh, IoTrash, IoCreate } from "react-icons/io5";

import VuiBox from "components/VuiBox";
import VuiTypography from "components/VuiTypography";
import VuiButton from "components/VuiButton";
import VuiAlert from "components/VuiAlert";
import VuiInput from "components/VuiInput";

const API_BASE = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

const cardColumns = [
  { key: "card_number", label: "Card #", width: "12%" },
  { key: "player_name", label: "Player(s)", width: "32%" },
  { key: "team", label: "Team(s)", width: "24%" },
  { key: "flags", label: "Flags", width: "16%" },
  { key: "notes", label: "Notes", width: "16%" },
];

export default function ManageChecklistsPanel({
  allowDelete = true,
  allowEdit = true,
  showRefresh = true,
  title = "Manage Checklists",
  subtitle = "Review approved checklists",
}) {
  const [summary, setSummary] = useState([]);
  const [loading, setLoading] = useState(true);
  const [alert, setAlert] = useState(null);
  const [openYear, setOpenYear] = useState(null);
  const [openSetsSection, setOpenSetsSection] = useState(null);
  const [openParallelsSection, setOpenParallelsSection] = useState(null);
  const [openChecklistId, setOpenChecklistId] = useState(null);
  const [details, setDetails] = useState({});

  // Edit modal state
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editingChecklist, setEditingChecklist] = useState(null);
  const [editForm, setEditForm] = useState({ year: "", product_name: "", set_type_name: "", display_name: "" });

  const fetchSummary = async () => {
    setLoading(true);
    setAlert(null);
    try {
      const res = await axios.get(`${API_BASE}/checklists/library/summary`);
      setSummary(res.data || []);
    } catch (err) {
      console.error("Failed to load checklist summary", err);
      setAlert({ type: "error", message: "Unable to load checklists. Please try again." });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  const groupedYears = useMemo(() => {
    const yearMap = new Map();

    summary.forEach((product) => {
      if (!yearMap.has(product.year)) {
        yearMap.set(product.year, {
          year: product.year,
          products: [],
          totalChecklists: 0
        });
      }

      const yearBucket = yearMap.get(product.year);
      yearBucket.products.push(product);
      yearBucket.totalChecklists += product.checklists.length;
    });

    return Array.from(yearMap.values())
      .sort((a, b) => parseInt(b.year, 10) - parseInt(a.year, 10));
  }, [summary]);

  const fetchChecklistDetail = async (checklistId) => {
    setDetails((prev) => ({
      ...prev,
      [checklistId]: { ...(prev[checklistId] || {}), loading: true, error: null },
    }));
    try {
      const res = await axios.get(`${API_BASE}/checklists/library/${checklistId}`);
      setDetails((prev) => ({
        ...prev,
        [checklistId]: { loading: false, data: res.data },
      }));
    } catch (err) {
      console.error("Failed to load checklist detail", err);
      setDetails((prev) => ({
        ...prev,
        [checklistId]: { loading: false, error: "Failed to load cards. Please try again." },
      }));
    }
  };

  const toggleChecklist = (checklistId) => {
    const opening = openChecklistId !== checklistId;
    setOpenChecklistId(opening ? checklistId : null);
    if (opening && !details[checklistId]) {
      fetchChecklistDetail(checklistId);
    }
  };

  const handleEdit = (checklist) => {
    setEditingChecklist(checklist);
    setEditForm({
      year: checklist.year,
      product_name: checklist.product_name,
      set_type_name: checklist.set_type,
      display_name: checklist.display_name,
    });
    setEditModalOpen(true);
  };

  const handleUpdateChecklist = async () => {
    if (!editingChecklist) return;

    try {
      await axios.patch(`${API_BASE}/checklists/library/${editingChecklist.id}`, {
        year: parseInt(editForm.year),
        product_name: editForm.product_name,
        set_type_name: editForm.set_type_name,
        display_name: editForm.display_name,
      });

      setAlert({ type: "success", message: "Checklist updated successfully!" });
      setEditModalOpen(false);
      setEditingChecklist(null);
      fetchSummary();
    } catch (err) {
      console.error("Failed to update checklist", err);
      setAlert({ type: "error", message: "Unable to update checklist. Please try again." });
    }
  };

  const handleDelete = async (checklist) => {
    if (!allowDelete) return;
    const confirmed = window.confirm(`Delete ${checklist.year} ${checklist.product_name} ${checklist.display_name}?`);
    if (!confirmed) return;

    try {
      await axios.delete(`${API_BASE}/checklists/library/${checklist.id}`);
      fetchSummary();
      setDetails((prev) => {
        const next = { ...prev };
        delete next[checklist.id];
        return next;
      });
      setOpenChecklistId(null);
      setAlert({ type: "success", message: "Checklist deleted." });
    } catch (err) {
      console.error("Failed to delete checklist", err);
      setAlert({ type: "error", message: "Unable to delete checklist. Please try again." });
    }
  };

  useEffect(() => {
    if (!alert) return;
    const timer = setTimeout(() => setAlert(null), 4000);
    return () => clearTimeout(timer);
  }, [alert]);

  const cardGridTemplate = cardColumns.map((c) => c.width).join(" ");

  return (
    <VuiBox>
      <VuiBox mb={3} display="flex" justifyContent="space-between" alignItems="center" flexWrap="wrap" gap={2}>
        <VuiBox>
          <VuiTypography variant="h4" color="white" fontWeight="bold" mb={1}>
            {title}
          </VuiTypography>
          <VuiTypography variant="body2" color="text">
            {subtitle}
          </VuiTypography>
        </VuiBox>
        {showRefresh && (
          <VuiButton color="info" onClick={fetchSummary} sx={{ display: "inline-flex", alignItems: "center", gap: "6px" }}>
            <IoRefresh size={16} />
            Refresh
          </VuiButton>
        )}
      </VuiBox>

      {alert && (
        <VuiBox mb={2}>
          <VuiAlert color={alert.type === "error" ? "error" : "success"}>{alert.message}</VuiAlert>
        </VuiBox>
      )}

      {loading ? (
        <VuiBox
          sx={{
            background: "linear-gradient(127deg, rgba(6,11,40,0.94), rgba(10,14,35,0.55))",
            borderRadius: "15px",
            border: "1px solid rgba(255,255,255,0.08)",
            py: 5,
            display: "flex",
            justifyContent: "center",
          }}
        >
          <CircularProgress sx={{ color: "#0075ff" }} size={28} />
        </VuiBox>
      ) : groupedYears.length === 0 ? (
        <VuiBox
          sx={{
            background: "linear-gradient(127deg, rgba(6,11,40,0.94), rgba(10,14,35,0.55))",
            borderRadius: "15px",
            border: "1px solid rgba(255,255,255,0.08)",
            textAlign: "center",
            py: 4,
          }}
        >
          <VuiTypography variant="body2" color="text">
            No checklists have been approved yet.
          </VuiTypography>
        </VuiBox>
      ) : (
        groupedYears.map((yearBucket) => {
          const isYearOpen = openYear === yearBucket.year;
          return (
            <VuiBox
              key={yearBucket.year}
              sx={{
                borderRadius: "20px",
                border: "2px solid rgba(0,117,255,0.3)",
                background: "linear-gradient(135deg, rgba(0,117,255,0.08), rgba(6,11,40,0.95))",
                mb: 3,
                overflow: "hidden",
                boxShadow: "0 8px 32px rgba(0,117,255,0.15)",
              }}
            >
              {/* Year Card Header */}
              <VuiBox
                sx={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  px: 4,
                  py: 3,
                  cursor: "pointer",
                  background: "linear-gradient(90deg, rgba(0,117,255,0.12), rgba(10,14,35,0.85))",
                  borderBottom: isYearOpen ? "1px solid rgba(0,117,255,0.2)" : "none",
                }}
                onClick={() => {
                  setOpenYear(isYearOpen ? null : yearBucket.year);
                  setOpenSetsSection(null);
                  setOpenParallelsSection(null);
                  setOpenChecklistId(null);
                }}
              >
                <VuiBox display="flex" alignItems="center" gap={3}>
                  <VuiBox
                    sx={{
                      background: "linear-gradient(135deg, #0075ff, #0052cc)",
                      borderRadius: "12px",
                      padding: "16px 24px",
                      boxShadow: "0 4px 20px rgba(0,117,255,0.4)",
                    }}
                  >
                    <VuiTypography variant="h2" color="white" fontWeight="bold" sx={{ letterSpacing: "2px" }}>
                      {yearBucket.year}
                    </VuiTypography>
                  </VuiBox>
                  <VuiBox>
                    <VuiTypography variant="h6" color="white" fontWeight="bold">
                      {yearBucket.products.length} {yearBucket.products.length === 1 ? "Product" : "Products"}
                    </VuiTypography>
                    <VuiTypography variant="caption" color="text" sx={{ mt: 0.5, display: "block" }}>
                      {yearBucket.totalChecklists} {yearBucket.totalChecklists === 1 ? "set" : "sets"} total
                    </VuiTypography>
                  </VuiBox>
                </VuiBox>
                {isYearOpen ? <IoChevronUp size={24} color="#0075ff" /> : <IoChevronDown size={24} color="#0075ff" />}
              </VuiBox>

              <Collapse in={isYearOpen} timeout="auto" unmountOnExit>
                <VuiBox px={4} py={3} display="flex" flexDirection="column" gap={3}>
                  {yearBucket.products.map((product) => {
                    const isSetsOpen = openSetsSection === product.product_id;
                    const isParallelsOpen = openParallelsSection === product.product_id;
                    return (
                      <VuiBox
                        key={product.product_id}
                        sx={{
                          border: "1px solid rgba(255,255,255,0.15)",
                          borderRadius: "16px",
                          background: "linear-gradient(135deg, rgba(10,14,35,0.8), rgba(6,11,40,0.95))",
                          overflow: "hidden",
                          boxShadow: "0 4px 20px rgba(0,0,0,0.3)",
                        }}
                      >
                        {/* Product Name Header */}
                        <VuiBox
                          px={3}
                          py={2}
                          sx={{
                            background: "rgba(0,117,255,0.05)",
                            borderBottom: "1px solid rgba(255,255,255,0.1)",
                          }}
                        >
                          <VuiTypography variant="h5" color="white" fontWeight="bold">
                            {product.product_name}
                          </VuiTypography>
                        </VuiBox>

                        {/* Sets Section Clickable Header */}
                        <VuiBox
                          px={3}
                          py={1.5}
                          display="flex"
                          justifyContent="space-between"
                          alignItems="center"
                          sx={{
                            cursor: "pointer",
                            background: "rgba(0,117,255,0.03)",
                            borderBottom: "1px solid rgba(255,255,255,0.05)",
                            transition: "all 0.2s",
                            "&:hover": {
                              background: "rgba(0,117,255,0.08)",
                            },
                          }}
                          onClick={() => {
                            setOpenSetsSection(isSetsOpen ? null : product.product_id);
                            setOpenChecklistId(null);
                          }}
                        >
                          <VuiBox>
                            <VuiTypography variant="button" color="#0075ff" fontWeight="bold">
                              {product.checklists.length} {product.checklists.length === 1 ? "Set" : "Sets"}
                            </VuiTypography>
                            <VuiTypography variant="caption" color="text" sx={{ fontSize: "10px", fontStyle: "italic", ml: 1 }}>
                              Click to View Sets
                            </VuiTypography>
                          </VuiBox>
                          {isSetsOpen ? <IoChevronUp size={18} color="#0075ff" /> : <IoChevronDown size={18} color="#0075ff" />}
                        </VuiBox>

                        <Collapse in={isSetsOpen} timeout="auto" unmountOnExit>
                          <VuiBox px={3} py={2}>
                            <VuiBox display="flex" flexDirection="column" gap={1.5}>
                                {product.checklists.map((checklist) => {
                                  const isChecklistOpen = openChecklistId === checklist.id;
                                  const detail = details[checklist.id] || {};
                                  return (
                                    <VuiBox key={checklist.id}>
                                      <VuiBox
                                        sx={{
                                          backgroundColor: "rgba(255,255,255,0.04)",
                                          borderRadius: "12px",
                                          padding: "14px 18px",
                                          display: "flex",
                                          justifyContent: "space-between",
                                          alignItems: "center",
                                          cursor: "pointer",
                                          border: "1px solid rgba(255,255,255,0.06)",
                                          transition: "all 0.2s",
                                          "&:hover": {
                                            backgroundColor: "rgba(255,255,255,0.08)",
                                            borderColor: "rgba(0,117,255,0.3)",
                                          },
                                        }}
                                        onClick={() => toggleChecklist(checklist.id)}
                                      >
                                        <VuiBox>
                                          <VuiTypography variant="button" color="white" fontWeight="bold">
                                            {checklist.display_name}
                                          </VuiTypography>
                                          <VuiTypography variant="caption" color="text" sx={{ mt: 0.8, display: "block" }}>
                                            {checklist.card_count} cards
                                            {checklist.card_count_declared ? ` / ${checklist.card_count_declared} expected` : ""}
                                          </VuiTypography>
                                        </VuiBox>
                                        <VuiBox display="flex" alignItems="center" gap={1}>
                                          {allowEdit && (
                                            <VuiButton
                                              color="info"
                                              size="small"
                                              onClick={(e) => {
                                                e.stopPropagation();
                                                handleEdit(checklist);
                                              }}
                                              sx={{ display: "inline-flex", alignItems: "center", gap: "6px" }}
                                            >
                                              <IoCreate size={14} />
                                              Edit
                                            </VuiButton>
                                          )}
                                          {allowDelete && (
                                            <VuiButton
                                              color="error"
                                              size="small"
                                              onClick={(e) => {
                                                e.stopPropagation();
                                                handleDelete(checklist);
                                              }}
                                              sx={{ display: "inline-flex", alignItems: "center", gap: "6px" }}
                                            >
                                              <IoTrash size={14} />
                                              Delete
                                            </VuiButton>
                                          )}
                                          {isChecklistOpen ? (
                                            <IoChevronUp size={16} color="#a0aec0" />
                                          ) : (
                                            <IoChevronDown size={16} color="#a0aec0" />
                                          )}
                                        </VuiBox>
                                      </VuiBox>

                                      <Collapse in={isChecklistOpen} timeout="auto" unmountOnExit>
                                        <VuiBox
                                          sx={{
                                            borderRadius: "14px",
                                            border: "1px solid rgba(255,255,255,0.08)",
                                            background: "rgba(6,11,40,0.85)",
                                            mt: 1.5,
                                          }}
                                        >
                                          {detail.loading ? (
                                            <VuiBox sx={{ display: "flex", alignItems: "center", gap: 1, py: 2, px: 3 }}>
                                              <CircularProgress sx={{ color: "#0075ff" }} size={18} />
                                              <VuiTypography variant="caption" color="text">
                                                Loading cards...
                                              </VuiTypography>
                                            </VuiBox>
                                          ) : detail.error ? (
                                            <VuiAlert color="error">{detail.error}</VuiAlert>
                                          ) : detail.data ? (
                                            <>
                                              <VuiBox
                                                sx={{
                                                  display: "grid",
                                                  gridTemplateColumns: cardGridTemplate,
                                                  backgroundColor: "rgba(6,11,40,0.97)",
                                                  px: 3,
                                                  py: 1.5,
                                                  borderBottom: "1px solid rgba(255,255,255,0.14)",
                                                }}
                                              >
                                                {cardColumns.map((col) => (
                                                  <VuiTypography
                                                    key={col.key}
                                                    variant="caption"
                                                    color="white"
                                                    fontWeight="bold"
                                                    sx={{ textTransform: "uppercase", letterSpacing: "0.8px" }}
                                                  >
                                                    {col.label}
                                                  </VuiTypography>
                                                ))}
                                              </VuiBox>
                                              <VuiBox sx={{ maxHeight: 360, overflowY: "auto" }}>
                                                {detail.data.cards.length === 0 ? (
                                                  <VuiBox sx={{ textAlign: "center", py: 3 }}>
                                                    <VuiTypography variant="body2" color="text">
                                                      No cards were parsed for this checklist.
                                                    </VuiTypography>
                                                  </VuiBox>
                                                ) : (
                                                  detail.data.cards.map((card) => (
                                                    <VuiBox
                                                      key={card.id}
                                                      sx={{
                                                        display: "grid",
                                                        gridTemplateColumns: cardGridTemplate,
                                                        px: 3,
                                                        py: 1.25,
                                                        borderBottom: "1px solid rgba(255,255,255,0.04)",
                                                      }}
                                                    >
                                                      <VuiTypography variant="button" color="white">
                                                        {card.card_number}
                                                      </VuiTypography>
                                                      <VuiTypography variant="button" color="white">
                                                        {card.player_name || "-"}
                                                      </VuiTypography>
                                                      <VuiTypography variant="button" color="text">
                                                        {card.team || "-"}
                                                      </VuiTypography>
                                                      <VuiTypography variant="caption" color="text">
                                                        {Array.isArray(card.flags) && card.flags.length > 0
                                                          ? card.flags.join(", ")
                                                          : "-"}
                                                      </VuiTypography>
                                                      <VuiTypography variant="caption" color="text">
                                                        {card.notes || "-"}
                                                      </VuiTypography>
                                                    </VuiBox>
                                                  ))
                                                )}
                                              </VuiBox>
                                            </>
                                          ) : null}
                                        </VuiBox>
                                      </Collapse>
                                    </VuiBox>
                                  );
                                })}
                              </VuiBox>
                            </VuiBox>
                        </Collapse>

                        {/* Parallels Section Clickable Header */}
                        {product.parallels && product.parallels.length > 0 && (
                          <>
                            <VuiBox
                              px={3}
                              py={1.5}
                              display="flex"
                              justifyContent="space-between"
                              alignItems="center"
                              sx={{
                                cursor: "pointer",
                                background: "rgba(0,217,255,0.03)",
                                borderBottom: isParallelsOpen ? "none" : "1px solid rgba(255,255,255,0.05)",
                                transition: "all 0.2s",
                                "&:hover": {
                                  background: "rgba(0,217,255,0.08)",
                                },
                              }}
                              onClick={() => {
                                setOpenParallelsSection(isParallelsOpen ? null : product.product_id);
                              }}
                            >
                              <VuiBox>
                                <VuiTypography variant="button" color="#00d9ff" fontWeight="bold">
                                  {product.parallels.length} {product.parallels.length === 1 ? "Parallel" : "Parallels"}
                                </VuiTypography>
                                <VuiTypography variant="caption" color="text" sx={{ fontSize: "10px", fontStyle: "italic", ml: 1 }}>
                                  Click to View Parallels
                                </VuiTypography>
                              </VuiBox>
                              {isParallelsOpen ? <IoChevronUp size={18} color="#00d9ff" /> : <IoChevronDown size={18} color="#00d9ff" />}
                            </VuiBox>

                            <Collapse in={isParallelsOpen} timeout="auto" unmountOnExit>
                              <VuiBox px={3} py={2}>
                                <VuiTypography variant="caption" color="text" mb={1.5} display="block">
                                  Visual reference images coming soon!
                                </VuiTypography>
                                <VuiBox display="flex" flexWrap="wrap" gap={1}>
                                  {[...product.parallels]
                                    .sort((a, b) => {
                                      // Nulls/undefined first
                                      if (!a.print_run && !b.print_run) return 0;
                                      if (!a.print_run) return -1;
                                      if (!b.print_run) return 1;
                                      // Then sort by print_run ascending
                                      return a.print_run - b.print_run;
                                    })
                                    .map((parallel) => (
                                    <VuiBox
                                      key={parallel.id}
                                      sx={{
                                        background: "linear-gradient(135deg, rgba(0,217,255,0.15), rgba(0,117,255,0.08))",
                                        border: "1px solid rgba(0,217,255,0.3)",
                                        borderRadius: "8px",
                                        padding: "6px 10px",
                                        minWidth: "70px",
                                        maxWidth: "120px",
                                        boxShadow: "0 1px 4px rgba(0,217,255,0.2)",
                                      }}
                                    >
                                      <VuiTypography variant="caption" color="white" fontWeight="bold" sx={{ display: "block", mb: 0.3, fontSize: "11px" }}>
                                        {parallel.name}
                                      </VuiTypography>
                                      <VuiBox display="flex" flexDirection="column" gap={0.2}>
                                        {parallel.print_run && (
                                          <VuiTypography variant="caption" color="#00d9ff" fontWeight="bold" sx={{ fontSize: "10px" }}>
                                            /{parallel.print_run}
                                          </VuiTypography>
                                        )}
                                        {parallel.exclusive && (
                                          <VuiTypography variant="caption" color="text" sx={{ fontSize: "9px" }}>
                                            {parallel.exclusive}
                                          </VuiTypography>
                                        )}
                                      </VuiBox>
                                    </VuiBox>
                                  ))}
                                </VuiBox>
                              </VuiBox>
                            </Collapse>
                          </>
                        )}
                      </VuiBox>
                    );
                  })}
                </VuiBox>
              </Collapse>
            </VuiBox>
          );
        })
      )}

      {/* Edit Modal */}
      <Modal
        open={editModalOpen}
        onClose={() => setEditModalOpen(false)}
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <VuiBox
          sx={{
            background: "linear-gradient(127deg, rgba(6,11,40,0.96), rgba(10,14,35,0.9))",
            borderRadius: "15px",
            padding: "32px",
            width: "90%",
            maxWidth: "600px",
            border: "1px solid rgba(255,255,255,0.12)",
            boxShadow: "0 20px 60px rgba(0,0,0,0.5)",
          }}
        >
          <VuiTypography variant="h5" color="white" fontWeight="bold" mb={3}>
            Edit Checklist
          </VuiTypography>

          <VuiBox display="flex" flexDirection="column" gap={2.5}>
            <VuiBox>
              <VuiTypography variant="caption" color="white" fontWeight="bold" mb={1}>
                Year
              </VuiTypography>
              <VuiInput
                type="number"
                value={editForm.year}
                onChange={(e) => setEditForm({ ...editForm, year: e.target.value })}
                placeholder="e.g., 2024"
              />
            </VuiBox>

            <VuiBox>
              <VuiTypography variant="caption" color="white" fontWeight="bold" mb={1}>
                Product Name
              </VuiTypography>
              <VuiInput
                value={editForm.product_name}
                onChange={(e) => setEditForm({ ...editForm, product_name: e.target.value })}
                placeholder="e.g., Topps Series 1"
              />
            </VuiBox>

            <VuiBox>
              <VuiTypography variant="caption" color="white" fontWeight="bold" mb={1}>
                Set Type
              </VuiTypography>
              <VuiInput
                value={editForm.set_type_name}
                onChange={(e) => setEditForm({ ...editForm, set_type_name: e.target.value })}
                placeholder="e.g., Base, Insert, Autograph"
              />
            </VuiBox>

            <VuiBox>
              <VuiTypography variant="caption" color="white" fontWeight="bold" mb={1}>
                Display Name
              </VuiTypography>
              <VuiInput
                value={editForm.display_name}
                onChange={(e) => setEditForm({ ...editForm, display_name: e.target.value })}
                placeholder="e.g., Base Set"
              />
            </VuiBox>

            <VuiBox display="flex" gap={2} mt={2}>
              <VuiButton
                color="info"
                onClick={handleUpdateChecklist}
                sx={{ flex: 1 }}
              >
                Save Changes
              </VuiButton>
              <VuiButton
                color="secondary"
                onClick={() => setEditModalOpen(false)}
                sx={{ flex: 1 }}
              >
                Cancel
              </VuiButton>
            </VuiBox>
          </VuiBox>
        </VuiBox>
      </Modal>
    </VuiBox>
  );
}
