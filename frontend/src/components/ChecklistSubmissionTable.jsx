
import React, { useEffect, useMemo, useState } from "react";
import axios from "axios";
import VuiBox from "components/VuiBox";
import VuiTypography from "components/VuiTypography";
import VuiButton from "components/VuiButton";
import VuiAlert from "components/VuiAlert";
import { Tabs, Tab, CircularProgress, Dialog, DialogTitle, DialogContent, DialogActions } from "@mui/material";

const API_BASE = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

const statusColors = {
  pending: "#f5a623",
  approved: "#01b574",
  rejected: "#e31a1a",
};

function StatusTag({ status }) {
  return (
    <VuiBox
      sx={{
        display: "inline-flex",
        alignItems: "center",
        px: 1.5,
        py: 0.5,
        borderRadius: "999px",
        border: `1px solid ${statusColors[status] || "#a0aec0"}`,
        color: statusColors[status] || "#a0aec0",
        fontSize: "12px",
        fontWeight: "bold",
        textTransform: "capitalize",
      }}
    >
      {status}
    </VuiBox>
  );
}

const submissionColumns = [
  { key: "id", label: "ID", width: "8%", align: "center", render: (item) => `#${item.id}` },
  { key: "product", label: "Product", width: "28%", align: "left", render: (item) => `${item.year} ${item.product_name}` },
  { key: "type", label: "Type", width: "16%", align: "left", render: (item) => `${item.set_type_name} (${item.submission_type})` },
  { key: "cards", label: "Cards", width: "12%", align: "center", render: (item) => item.card_count_declared ?? item.parsed_data.length },
  { key: "submitted_at", label: "Submitted", width: "16%", align: "left", render: (item) => new Date(item.submitted_at).toLocaleString() },
  { key: "status", label: "Status", width: "10%", align: "center", render: (item) => <StatusTag status={item.status} /> },
  { key: "actions", label: "Actions", width: "10%", align: "center", render: () => null },
];

export default function ChecklistSubmissionTable() {
  const [submissions, setSubmissions] = useState([]);
  const [filter, setFilter] = useState("pending");
  const [loading, setLoading] = useState(true);
  const [alert, setAlert] = useState({ show: false, type: "info", message: "" });
  const [detail, setDetail] = useState(null);
  const [notes, setNotes] = useState("");

  const fetchSubmissions = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/checklists/submissions`);
      setSubmissions(res.data);
      setAlert({ show: false, type: "info", message: "" });
    } catch (err) {
      console.error("Failed to load submissions", err);
      setAlert({ show: true, type: "error", message: "Unable to load submissions. Please try again." });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSubmissions();
  }, []);

  const changeStatus = async (submission, status) => {
    try {
      await axios.patch(`${API_BASE}/checklists/submissions/${submission.id}/status`, {
        status,
        admin_notes: notes || undefined,
      });
      setSubmissions((prev) =>
        prev.map((item) => (item.id === submission.id ? { ...item, status, admin_notes: notes, reviewed_at: new Date().toISOString() } : item))
      );
      setAlert({ show: true, type: "success", message: `Submission #${submission.id} marked as ${status}.` });
      setDetail(null);
      setNotes("");
    } catch (err) {
      console.error("Failed to update submission", err);
      setAlert({ show: true, type: "error", message: "Failed to update submission status. Please try again." });
    }
  };

  const filteredSubmissions = useMemo(() => {
    if (filter === "all") return submissions;
    return submissions.filter((sub) => sub.status === filter);
  }, [filter, submissions]);

  const submissionRowColor = (status) => {
    switch ((status || "").toLowerCase()) {
      case "pending":
        return "rgba(255, 181, 71, 0.15)";
      case "approved":
        return "rgba(1, 181, 116, 0.15)";
      case "rejected":
        return "rgba(227, 26, 26, 0.15)";
      default:
        return "rgba(255,255,255,0.04)";
    }
  };

  const gridTemplate = submissionColumns.map((col) => col.width).join(" ");

  return (
    <VuiBox mb={4}>
      <VuiTypography variant="h4" color="white" fontWeight="bold" mb={1}>
        Checklist Submissions
      </VuiTypography>
      <VuiTypography variant="body2" color="text" mb={3}>
        Review parsed checklist uploads and approve or reject them.
      </VuiTypography>

      {alert.show && (
        <VuiBox mb={3}>
          <VuiAlert color={alert.type === "error" ? "error" : "success"}>{alert.message}</VuiAlert>
        </VuiBox>
      )}

      <Tabs
        value={filter}
        onChange={(e, value) => setFilter(value)}
        sx={{
          mb: 3,
          background: "linear-gradient(127.09deg, rgba(6,11,40,0.9), rgba(10,14,35,0.6))",
          borderRadius: "12px",
          padding: "4px",
          "& .MuiTabs-indicator": { backgroundColor: "#0075ff", height: "3px", borderRadius: "999px" },
          "& .MuiTab-root": {
            color: "#a0aec0",
            textTransform: "none",
            fontWeight: 500,
            minWidth: "auto",
            padding: "10px 22px",
            borderRadius: "10px",
          },
          "& .MuiTab-root.Mui-selected": {
            color: "#fff !important",
            backgroundColor: "rgba(255,255,255,0.08)",
          },
        }}
      >
        <Tab label="Pending" value="pending" />
        <Tab label="Approved" value="approved" />
        <Tab label="Rejected" value="rejected" />
        <Tab label="All" value="all" />
      </Tabs>

      <VuiBox
        sx={{
          borderRadius: "16px",
          border: "1px solid rgba(255,255,255,0.1)",
          background: "linear-gradient(127.09deg, rgba(6, 11, 40, 0.94) 19.41%, rgba(10, 14, 35, 0.49) 76.65%)",
          overflow: "hidden",
        }}
      >
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
          {submissionColumns.map((col) => (
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

        {loading ? (
          <VuiBox display="flex" justifyContent="center" alignItems="center" py={6}>
            <CircularProgress sx={{ color: "#0075ff" }} />
          </VuiBox>
        ) : filteredSubmissions.length === 0 ? (
          <VuiBox textAlign="center" py={4}>
            <VuiTypography variant="body2" color="text">
              No submissions found for this filter.
            </VuiTypography>
          </VuiBox>
        ) : (
          <VuiBox sx={{ maxHeight: 420, overflowY: "auto" }}>
            {filteredSubmissions.map((submission) => (
              <VuiBox
                key={submission.id}
                sx={{
                  display: "grid",
                  gridTemplateColumns: gridTemplate,
                  px: 3,
                  py: 1.25,
                  backgroundColor: submissionRowColor(submission.status),
                  borderBottom: "1px solid rgba(255,255,255,0.05)",
                  alignItems: "center",
                }}
              >
                {submissionColumns.map((col) => (
                  <VuiBox key={col.key} sx={{ textAlign: col.align || "left" }}>
                    {col.key === "actions" ? (
                      <VuiBox sx={{ display: "flex", justifyContent: "center", gap: 1 }}>
                        <VuiButton color="info" variant="outlined" size="small" onClick={() => setDetail(submission)}>
                          View
                        </VuiButton>
                        {submission.status !== "approved" && (
                          <VuiButton color="success" size="small" onClick={() => changeStatus(submission, "approved")}>
                            Approve
                          </VuiButton>
                        )}
                      </VuiBox>
                    ) : col.key === "status" ? (
                      col.render(submission)
                    ) : (
                      <VuiTypography variant="button" color="white" sx={{ fontSize: "14px" }}>
                        {col.render(submission)}
                      </VuiTypography>
                    )}
                  </VuiBox>
                ))}
              </VuiBox>
            ))}
          </VuiBox>
        )}
      </VuiBox>

      <Dialog
        open={Boolean(detail)}
        onClose={() => {
          setDetail(null);
          setNotes("");
        }}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            background: "linear-gradient(127.09deg, rgba(6, 11, 40, 0.94), rgba(10, 14, 35, 0.9))",
            color: "#fff",
            borderRadius: "16px",
          },
        }}
      >
        {detail && (
          <>
            <DialogTitle>
              Submission #{detail.id} - {detail.year} {detail.product_name}
            </DialogTitle>
            <DialogContent dividers>
              <VuiTypography variant="button" color="white" fontWeight="bold">
                Type:
              </VuiTypography>{" "}
              <VuiTypography variant="caption" color="text">
                {detail.set_type_name} ({detail.submission_type})
              </VuiTypography>
              <VuiBox my={2}>
        <VuiBox
          component="pre"
          sx={{
            width: "100%",
            marginTop: "8px",
            borderRadius: "8px",
            border: "1px solid rgba(255,255,255,0.2)",
            background: "rgba(0,0,0,0.25)",
            color: "#fff",
            padding: "12px",
            maxHeight: "220px",
            overflowY: "auto",
            fontFamily: "monospace",
            whiteSpace: "pre-wrap",
          }}
        >
          {detail.raw_text}
        </VuiBox>
              </VuiBox>
              <VuiBox mb={2}>
                <VuiTypography variant="button" color="white" fontWeight="bold">
                  Notes to attach
                </VuiTypography>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Optional admin notes"
                  rows={3}
                  style={{
                    width: "100%",
                    marginTop: "8px",
                    borderRadius: "8px",
                    border: "1px solid rgba(255,255,255,0.2)",
                    background: "rgba(0,0,0,0.15)",
                    color: "#fff",
                    padding: "12px",
                  }}
                />
              </VuiBox>
            </DialogContent>
            <DialogActions sx={{ p: 2 }}>
              <VuiButton variant="outlined" color="secondary" onClick={() => setDetail(null)}>
                Close
              </VuiButton>
              {detail.status !== "approved" && (
                <VuiButton color="success" onClick={() => changeStatus(detail, "approved")}>
                  Approve
                </VuiButton>
              )}
            </DialogActions>
          </>
        )}
      </Dialog>
    </VuiBox>
  );
}
