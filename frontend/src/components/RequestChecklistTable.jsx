import React, { useEffect, useState } from "react";
import axios from "axios";
import { CircularProgress, Tabs, Tab } from "@mui/material";
import VuiBox from "components/VuiBox";
import VuiTypography from "components/VuiTypography";
import VuiButton from "components/VuiButton";
import VuiAlert from "components/VuiAlert";
import StatusBadge from "components/StatusBadge";

export default function RequestChecklistTable() {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [alert, setAlert] = useState({ show: false, type: "", message: "" });
  const [filter, setFilter] = useState("pending"); // "pending", "completed", "all"

  const fetchRequests = async () => {
    try {
      const res = await axios.get("http://127.0.0.1:8000/checklist/requests");
      setRequests(res.data);
      setAlert({ show: false, type: "", message: "" });
    } catch (err) {
      console.error("❌ Error loading requests:", err);
      setAlert({
        show: true,
        type: "error",
        message: "Failed to load requests. Please refresh the page.",
      });
    } finally {
      setLoading(false);
    }
  };

  const completeRequest = async (id) => {
    try {
      await axios.patch(
        `http://127.0.0.1:8000/checklist/requests/${id}/status?status=completed`
      );
      setRequests((prev) =>
        prev.map((r) => (r.id === id ? { ...r, status: "completed" } : r))
      );
      setAlert({
        show: true,
        type: "success",
        message: "Request marked as completed successfully!",
      });

      // Auto-hide success message after 3 seconds
      setTimeout(() => {
        setAlert({ show: false, type: "", message: "" });
      }, 3000);
    } catch (err) {
      console.error("❌ Failed to complete request:", err);
      setAlert({
        show: true,
        type: "error",
        message: "Failed to complete request. Please try again.",
      });
    }
  };

  const deleteRequest = async (id) => {
    if (!window.confirm("Are you sure you want to delete this request? This action cannot be undone.")) {
      return;
    }

    try {
      await axios.delete(`http://127.0.0.1:8000/checklist/requests/${id}`);
      setRequests((prev) => prev.filter((r) => r.id !== id));
      setAlert({
        show: true,
        type: "success",
        message: "Request deleted successfully!",
      });

      // Auto-hide success message after 3 seconds
      setTimeout(() => {
        setAlert({ show: false, type: "", message: "" });
      }, 3000);
    } catch (err) {
      console.error("❌ Failed to delete request:", err);
      setAlert({
        show: true,
        type: "error",
        message: "Failed to delete request. Please try again.",
      });
    }
  };

  useEffect(() => {
    fetchRequests();
  }, []);

  // Filter requests based on selected tab
  const filteredRequests = requests.filter((req) => {
    if (filter === "pending") return req.status === "pending" || req.status === "approved";
    if (filter === "completed") return req.status === "completed";
    return true; // "all"
  });

  const rowBgForStatus = (status) => {
    switch ((status || "").toLowerCase()) {
      case "pending":
        return "rgba(255, 181, 71, 0.15)";
      case "approved":
      case "completed":
        return "rgba(1, 181, 116, 0.15)";
      case "rejected":
        return "rgba(227, 26, 26, 0.15)";
      default:
        return "rgba(255,255,255,0.04)";
    }
  };

  // Columns config to drive header/body and enforce widths
  const columns = [
    { key: 'set_name',     label: 'Set Name',     width: '25%', align: 'left' },
    { key: 'year',         label: 'Year',         width: '10%', align: 'left' },
    { key: 'manufacturer', label: 'Manufacturer', width: '15%', align: 'left' },
    { key: 'email',        label: 'Email',        width: '20%', align: 'left' },
    { key: 'status',       label: 'Status',       width: '12%', align: 'left' },
    { key: 'actions',      label: 'Actions',      width: '18%', align: 'center' },
  ];

  const gridTemplate = columns.map((col) => col.width).join(" ");

  return (
    <VuiBox>
      {alert.show && (
        <VuiBox mb={3}>
          <VuiAlert color={alert.type === "success" ? "success" : "error"}>
            {alert.message}
          </VuiAlert>
        </VuiBox>
      )}

      {/* Filter Tabs */}
      <VuiBox mb={3}>
        <Tabs
          value={filter}
          onChange={(e, newValue) => setFilter(newValue)}
          sx={{
            background: "linear-gradient(127.09deg, rgba(6,11,40,0.9), rgba(10,14,35,0.6))",
            borderRadius: "12px",
            padding: "4px",
            minHeight: "auto",
            "& .MuiTabs-indicator": {
              backgroundColor: "#0075ff",
              height: "3px",
              borderRadius: "999px",
            },
            "& .MuiTab-root": {
              color: "#a0aec0",
              fontWeight: 500,
              textTransform: "none",
              fontSize: "14px",
              minWidth: "auto",
              padding: "10px 20px",
              minHeight: "auto",
              borderRadius: "10px",
              transition: "all 0.2s ease",
            },
            "& .MuiTab-root.Mui-selected": {
              color: "#fff !important",
              backgroundColor: "rgba(255,255,255,0.08)",
            },
          }}
        >
          <Tab label="Pending" value="pending" />
          <Tab label="Completed" value="completed" />
          <Tab label="All" value="all" />
        </Tabs>
      </VuiBox>

      <VuiBox
        sx={{
          background: "linear-gradient(135deg, rgba(6,11,40,0.94), rgba(10,14,35,0.55))",
          borderRadius: "15px",
          border: "1px solid rgba(255,255,255,0.1)",
          overflow: "hidden",
        }}
      >
        {/* Header */}
        <VuiBox
          sx={{
            display: "grid",
            gridTemplateColumns: gridTemplate,
            backgroundColor: "rgba(6,11,40,0.96)",
            px: 3,
            py: 1.5,
            borderBottom: "1px solid rgba(255,255,255,0.1)",
          }}
        >
          {columns.map((col) => (
            <VuiTypography
              key={col.key}
              variant="caption"
              color="white"
              fontWeight="bold"
              sx={{ textTransform: "uppercase", letterSpacing: "0.8px", textAlign: col.align || "left" }}
            >
              {col.label}
            </VuiTypography>
          ))}
        </VuiBox>
        {/* CSS Grid body */}
        {loading ? (
          <VuiBox sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 3 }}>
            <CircularProgress sx={{ color: '#0075ff' }} size={28} />
          </VuiBox>
        ) : filteredRequests.length === 0 ? (
          <VuiBox sx={{ textAlign: 'center', py: 3 }}>
            <VuiTypography variant="body2" color="text">
              No {filter !== 'all' ? filter : ''} requests found
            </VuiTypography>
          </VuiBox>
        ) : (
          <VuiBox sx={{ maxHeight: 420, overflowY: "auto" }}>
            {filteredRequests.map((req, idx) => (
              <VuiBox
                key={req.id}
                sx={{
                  display: "grid",
                  gridTemplateColumns: gridTemplate,
                  px: 3,
                  py: 1.25,
                  alignItems: "center",
                  backgroundColor: rowBgForStatus(req.status),
                  borderBottom: "1px solid rgba(255,255,255,0.05)",
                }}
              >
                <VuiBox>
                  <VuiTypography variant="button" color="white" fontWeight="medium">
                    {req.set_name}
                  </VuiTypography>
                  {req.notes && (
                    <VuiTypography variant="caption" color="text" display="block">
                      {req.notes.substring(0, 50)}
                      {req.notes.length > 50 ? "..." : ""}
                    </VuiTypography>
                  )}
                </VuiBox>
                <VuiTypography variant="button" color="white">
                  {req.year}
                </VuiTypography>
                <VuiTypography variant="button" color="text">
                  {req.manufacturer || "-"}
                </VuiTypography>
                <VuiTypography variant="caption" color="text">
                  {req.email || "-"}
                </VuiTypography>
                <VuiBox sx={{ textAlign: "center" }}>
                  <StatusBadge status={req.status} />
                </VuiBox>
                <VuiBox sx={{ display: "flex", gap: 1, justifyContent: "center", flexWrap: "wrap" }}>
                  {req.status !== "completed" && (
                    <VuiButton color="success" size="small" onClick={() => completeRequest(req.id)} sx={{ minWidth: "80px" }}>
                      Complete
                    </VuiButton>
                  )}
                  <VuiButton color="error" size="small" onClick={() => deleteRequest(req.id)} sx={{ minWidth: "70px" }}>
                    Delete
                  </VuiButton>
                </VuiBox>
              </VuiBox>
            ))}
          </VuiBox>
        )}
      </VuiBox>
    </VuiBox>
  );
}
