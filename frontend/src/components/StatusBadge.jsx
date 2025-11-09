import React from "react";
import VuiBox from "components/VuiBox";
import VuiTypography from "components/VuiTypography";

export default function StatusBadge({ status }) {
  const getStatusColor = () => {
    switch (status?.toLowerCase()) {
      case "pending":
        return {
          bg: "rgba(251, 191, 36, 0.15)",
          border: "rgba(251, 191, 36, 0.4)",
          text: "#fbbf24",
        };
      case "approved":
        return {
          bg: "rgba(34, 197, 94, 0.15)",
          border: "rgba(34, 197, 94, 0.4)",
          text: "#22c55e",
        };
      case "completed":
        return {
          bg: "rgba(59, 130, 246, 0.15)",
          border: "rgba(59, 130, 246, 0.4)",
          text: "#3b82f6",
        };
      case "rejected":
        return {
          bg: "rgba(239, 68, 68, 0.15)",
          border: "rgba(239, 68, 68, 0.4)",
          text: "#ef4444",
        };
      default:
        return {
          bg: "rgba(156, 163, 175, 0.15)",
          border: "rgba(156, 163, 175, 0.4)",
          text: "#9ca3af",
        };
    }
  };

  const colors = getStatusColor();

  return (
    <VuiBox
      sx={{
        display: "inline-flex",
        alignItems: "center",
        px: 2,
        py: 0.5,
        borderRadius: "8px",
        backgroundColor: colors.bg,
        border: `1px solid ${colors.border}`,
      }}
    >
      <VuiTypography
        variant="caption"
        fontWeight="medium"
        sx={{ color: colors.text, textTransform: "capitalize" }}
      >
        {status || "Unknown"}
      </VuiTypography>
    </VuiBox>
  );
}
