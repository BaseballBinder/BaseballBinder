import React, { useState } from "react";
import axios from "axios";
import VuiBox from "components/VuiBox";
import VuiTypography from "components/VuiTypography";
import VuiButton from "components/VuiButton";
import VuiAlert from "components/VuiAlert";
import DashboardLayout from "examples/LayoutContainers/DashboardLayout";
import DashboardNavbar from "examples/Navbars/DashboardNavbar";
import Footer from "examples/Footer";
import ChecklistSummaryTable from "components/ChecklistSummaryTable";

function ManageChecklists() {
  const [rescanning, setRescanning] = useState(false);
  const [alert, setAlert] = useState({ show: false, type: "", message: "" });
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleRescan = async () => {
    setRescanning(true);
    setAlert({ show: false, type: "", message: "" });

    try {
      const response = await axios.post("http://127.0.0.1:8000/checklist/rescan");
      console.log("✅ Rescan response:", response.data);

      const message = response.data.message || "Checklists rescanned successfully!";
      const imported = response.data.imported || 0;
      const errors = response.data.errors || 0;

      setAlert({
        show: true,
        type: "success",
        message: `${message} (Imported: ${imported}${errors > 0 ? `, Errors: ${errors}` : ""})`,
      });

      // Trigger refresh of the table
      setRefreshTrigger(prev => prev + 1);

      // Auto-hide success message after 5 seconds
      setTimeout(() => {
        setAlert({ show: false, type: "", message: "" });
      }, 5000);
    } catch (error) {
      console.error("❌ Rescan error:", error);
      setAlert({
        show: true,
        type: "error",
        message: error.response?.data?.detail || "Failed to rescan checklists. Please try again.",
      });
    } finally {
      setRescanning(false);
    }
  };

  return (
    <DashboardLayout>
      <DashboardNavbar />
      <VuiBox py={3}>
        <VuiBox mb={3} display="flex" justifyContent="space-between" alignItems="center" flexWrap="wrap" gap={2}>
          <VuiBox>
            <VuiTypography variant="h3" color="white" fontWeight="bold" mb={1}>
              Manage Checklists
            </VuiTypography>
            <VuiTypography variant="body2" color="text">
              View imported checklists and rescan for new additions
            </VuiTypography>
          </VuiBox>
          <VuiButton
            color="info"
            onClick={handleRescan}
            disabled={rescanning}
            sx={{ height: "44px" }}
          >
            {rescanning ? "Scanning..." : "Rescan Folder"}
          </VuiButton>
        </VuiBox>

        {alert.show && (
          <VuiBox mb={3}>
            <VuiAlert color={alert.type === "success" ? "success" : "error"}>
              {alert.message}
            </VuiAlert>
          </VuiBox>
        )}

        <ChecklistSummaryTable refreshTrigger={refreshTrigger} />
      </VuiBox>
      <Footer />
    </DashboardLayout>
  );
}

export default ManageChecklists;
