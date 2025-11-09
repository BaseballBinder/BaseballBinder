/*!

=========================================================
* Vision UI Free React - v1.0.0
=========================================================

* Product Page: https://www.creative-tim.com/product/vision-ui-free-react
* Copyright 2021 Creative Tim (https://www.creative-tim.com/)
* Licensed under MIT (https://github.com/creativetimofficial/vision-ui-free-react/blob/master LICENSE.md)

* Design and Coded by Simmmple & Creative Tim

=========================================================

* The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

*/

// @mui material components
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Icon from "@mui/material/Icon";
import Link from "@mui/material/Link";

// Vision UI Dashboard React components
import VuiButton from "components/VuiButton";
import VuiBox from "components/VuiBox";
import VuiTypography from "components/VuiTypography";

// Custom styles for the SidenavCard
import { card, cardContent, cardIconBox, cardIcon } from "examples/Sidenav/styles/sidenavCard";

// Vision UI Dashboard React context
import { useVisionUIController } from "context";

function SidenavCard({ color, ...rest }) {
  const [controller] = useVisionUIController();
  const { miniSidenav, sidenavColor } = controller;

  return (
    <Card sx={(theme) => card(theme, { miniSidenav })}>
      <CardContent sx={(theme) => cardContent(theme, { sidenavColor })}>
        <VuiBox lineHeight={1} textAlign="center">
          <VuiBox
            sx={{
              background: 'linear-gradient(127.09deg, rgba(6, 11, 40, 0.94) 19.41%, rgba(10, 14, 35, 0.49) 76.65%)',
              borderRadius: '12px',
              padding: '40px 20px',
              border: '1px solid rgba(159, 122, 234, 0.4)',
              boxShadow: '0 8px 24px rgba(159, 122, 234, 0.3), 0 0 40px rgba(67, 24, 255, 0.2)',
              transition: 'all 0.3s ease',
              '&:hover': {
                boxShadow: '0 12px 32px rgba(159, 122, 234, 0.4), 0 0 60px rgba(67, 24, 255, 0.3)',
                transform: 'translateY(-2px)',
              },
            }}
          >
            <VuiTypography variant="h5" color="white" fontWeight="bold">
              Advertise Here
            </VuiTypography>
          </VuiBox>
        </VuiBox>
      </CardContent>
    </Card>
  );
}

export default SidenavCard;
