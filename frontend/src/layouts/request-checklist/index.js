import React from "react";

import RequestChecklistForm from "../../components/RequestChecklistForm";

import VuiBox from "components/VuiBox";
import DashboardLayout from "examples/LayoutContainers/DashboardLayout";
import DashboardNavbar from "examples/Navbars/DashboardNavbar";
import Footer from "examples/Footer";

function RequestChecklist() {
  return (
    <DashboardLayout>
      <DashboardNavbar />
      <VuiBox py={3}>
        <RequestChecklistForm />
      </VuiBox>
      <Footer />
    </DashboardLayout>
  );
}

export default RequestChecklist;
