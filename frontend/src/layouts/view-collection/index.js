import React from "react";
import VuiBox from "components/VuiBox";
import VuiTypography from "components/VuiTypography";
import DashboardLayout from "examples/LayoutContainers/DashboardLayout";
import DashboardNavbar from "examples/Navbars/DashboardNavbar";
import Footer from "examples/Footer";
import CollectionTable from "components/CollectionTable";

function ViewCollection() {
  return (
    <DashboardLayout>
      <DashboardNavbar />
      <VuiBox py={3}>
        <VuiBox mb={3}>
          <VuiTypography variant="h3" color="white" fontWeight="bold" mb={1}>
            My Collection
          </VuiTypography>
          <VuiTypography variant="body2" color="text">
            Browse and manage your baseball card collection
          </VuiTypography>
        </VuiBox>
        <CollectionTable />
      </VuiBox>
      <Footer />
    </DashboardLayout>
  );
}

export default ViewCollection;
