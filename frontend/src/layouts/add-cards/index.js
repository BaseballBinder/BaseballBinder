import React from "react";
import VuiBox from "components/VuiBox";
import DashboardLayout from "examples/LayoutContainers/DashboardLayout";
import DashboardNavbar from "examples/Navbars/DashboardNavbar";
import Footer from "examples/Footer";
import AddCardForm from "components/AddCardForm";

function AddCards() {
  return (
    <DashboardLayout>
      <DashboardNavbar />
      <VuiBox py={3}>
        <AddCardForm />
      </VuiBox>
      <Footer />
    </DashboardLayout>
  );
}

export default AddCards;
