import React from "react";

// Vision UI Dashboard React components
import VuiBox from "components/VuiBox";
import VuiTypography from "components/VuiTypography";
import DashboardLayout from "examples/LayoutContainers/DashboardLayout";
import DashboardNavbar from "examples/Navbars/DashboardNavbar";
import Footer from "examples/Footer";

function ImportChecklists() {
  return (
    <DashboardLayout>
      <DashboardNavbar />
      <VuiBox py={3}>
        <VuiTypography variant="h3" color="white" fontWeight="bold" mb={3}>
          Import Checklists
        </VuiTypography>
        <VuiBox
          sx={{
            background: 'linear-gradient(127.09deg, rgba(6, 11, 40, 0.94) 19.41%, rgba(10, 14, 35, 0.49) 76.65%)',
            borderRadius: '15px',
            padding: '40px',
            textAlign: 'center',
          }}
        >
          <VuiTypography variant="h5" color="text" mb={2}>
            Coming Soon
          </VuiTypography>
          <VuiTypography variant="body2" color="text">
            Import checklist files from your local system
          </VuiTypography>
        </VuiBox>
      </VuiBox>
      <Footer />
    </DashboardLayout>
  );
}

export default ImportChecklists;
