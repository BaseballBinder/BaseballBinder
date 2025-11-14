/**
 * ADMIN LOGIN - NOT YET ACTIVATED
 *
 * This is the admin login page.
 * To activate: Add to routes.js and update admin-dashboard to use ProtectedRoute
 */

import { useState } from "react";
// import { useHistory } from "react-router-dom"; // Uncomment when activating
// import { useAuth } from "context/AuthContext"; // Uncomment when activating
import VuiBox from "components/VuiBox";
import VuiTypography from "components/VuiTypography";
import VuiInput from "components/VuiInput";
import VuiButton from "components/VuiButton";
import VuiAlert from "components/VuiAlert";
import DashboardLayout from "examples/LayoutContainers/DashboardLayout";
import DashboardNavbar from "examples/Navbars/DashboardNavbar";
import Footer from "examples/Footer";
import { Card, Icon } from "@mui/material";

function AdminLogin() {
  // const history = useHistory(); // Uncomment when activating
  // const { login } = useAuth(); // Uncomment when activating
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    // UNCOMMENT THIS BLOCK WHEN ACTIVATING:
    /*
    const result = await login(password);
    if (result.success) {
      history.push("/admin-dashboard");
    } else {
      setError(result.message || "Invalid password");
    }
    */

    // TEMPORARY - Remove when activating
    console.log("Login attempt with password:", password);
    setError("Authentication system not yet activated");

    setLoading(false);
  };

  return (
    <DashboardLayout>
      <DashboardNavbar />
      <VuiBox py={3}>
        <VuiBox mb={3} display="flex" justifyContent="center">
          <Card sx={{ maxWidth: 500, width: "100%", p: 3 }}>
            <VuiBox mb={3} textAlign="center">
              <Icon fontSize="large" color="info" sx={{ fontSize: "60px !important", mb: 2 }}>
                lock
              </Icon>
              <VuiTypography variant="h3" color="white" fontWeight="bold" mb={1}>
                Admin Login
              </VuiTypography>
              <VuiTypography variant="body2" color="text">
                Enter admin password to access dashboard
              </VuiTypography>
            </VuiBox>

            {error && (
              <VuiBox mb={2}>
                <VuiAlert color="error">{error}</VuiAlert>
              </VuiBox>
            )}

            <form onSubmit={handleSubmit}>
              <VuiBox mb={2}>
                <VuiBox mb={1} ml={0.5}>
                  <VuiTypography component="label" variant="button" color="white" fontWeight="medium">
                    Password
                  </VuiTypography>
                </VuiBox>
                <VuiInput
                  type="password"
                  placeholder="Enter admin password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  sx={{
                    border: "1px solid rgba(255, 255, 255, 0.2) !important",
                  }}
                />
              </VuiBox>

              <VuiBox mt={4} mb={1}>
                <VuiButton color="info" fullWidth type="submit" disabled={loading || !password}>
                  {loading ? "Logging in..." : "Login"}
                </VuiButton>
              </VuiBox>
            </form>

            <VuiBox mt={3} textAlign="center">
              <VuiTypography variant="caption" color="text">
                Forgot your password? Contact the system administrator.
              </VuiTypography>
            </VuiBox>
          </Card>
        </VuiBox>
      </VuiBox>
      <Footer />
    </DashboardLayout>
  );
}

export default AdminLogin;
