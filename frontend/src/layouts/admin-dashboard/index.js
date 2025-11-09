import React from "react";
import RequestChecklistTable from "components/RequestChecklistTable";
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
        <RequestChecklistTable />
      </VuiBox>
      <Footer />
    </DashboardLayout>
  );
}

export default AdminDashboard;
