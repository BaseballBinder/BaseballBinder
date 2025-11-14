import React from "react";
import RequestChecklistTable from "components/RequestChecklistTable";
import ChecklistSubmissionTable from "components/ChecklistSubmissionTable";
import ManageChecklistsPanel from "components/ManageChecklistsPanel";
import VuiBox from "components/VuiBox";
import VuiTypography from "components/VuiTypography";
import DashboardLayout from "examples/LayoutContainers/DashboardLayout";
import DashboardNavbar from "examples/Navbars/DashboardNavbar";
import Footer from "examples/Footer";

function AdminDashboard() {
  return (
    <DashboardLayout>
      <DashboardNavbar />
      <VuiBox py={3}>
        <VuiBox mb={3}>
          <VuiTypography variant="h3" color="white" fontWeight="bold" mb={1}>
            Admin Dashboard
          </VuiTypography>
          <VuiTypography variant="body2" color="text">
            Manage and review checklist requests from users
          </VuiTypography>
        </VuiBox>
        <ChecklistSubmissionTable />

        <VuiBox mt={6}>
          <VuiTypography variant="h4" color="white" fontWeight="bold" mb={1}>
            Checklist Requests
          </VuiTypography>
          <VuiTypography variant="body2" color="text" mb={2}>
            Track community checklist asks, close them out when complete, or clean up old entries.
          </VuiTypography>
          <RequestChecklistTable />
        </VuiBox>

        <VuiBox mt={6}>
          <ManageChecklistsPanel
            allowDelete={true}
            allowEdit={true}
            showRefresh
            title="Manage Checklists"
            subtitle="Review approved checklists, drill into cards, or remove outdated uploads."
          />
        </VuiBox>
      </VuiBox>
      <Footer />
    </DashboardLayout>
  );
}

export default AdminDashboard;
