import React from "react";
import VuiBox from "components/VuiBox";
import DashboardLayout from "examples/LayoutContainers/DashboardLayout";
import DashboardNavbar from "examples/Navbars/DashboardNavbar";
import Footer from "examples/Footer";
import ManageChecklistsPanel from "components/ManageChecklistsPanel";

function ViewChecklists() {
  return (
    <DashboardLayout>
      <DashboardNavbar />
      <VuiBox py={3}>
        <ManageChecklistsPanel
          allowDelete={false}
          allowEdit={false}
          showRefresh
          title="Current Checklists"
          subtitle="Browse approved BaseballBinder checklists grouped by year."
        />
      </VuiBox>
      <Footer />
    </DashboardLayout>
  );
}

export default ViewChecklists;
