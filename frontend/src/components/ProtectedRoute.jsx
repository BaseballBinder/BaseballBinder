/**
 * PROTECTED ROUTE - NOT YET ACTIVATED
 *
 * This component protects admin routes, redirecting to login if not authenticated.
 * To activate: Replace Route with ProtectedRoute for admin-dashboard in App.js
 *
 * Example usage when activating:
 * <ProtectedRoute exact path="/admin-dashboard" component={AdminDashboard} />
 */

// import { Route, Redirect } from "react-router-dom"; // Uncomment when activating
// import { useAuth } from "context/AuthContext"; // Uncomment when activating
// import { CircularProgress } from "@mui/material"; // Uncomment when activating
// import VuiBox from "components/VuiBox"; // Uncomment when activating

// eslint-disable-next-line no-unused-vars
function ProtectedRoute({ component: Component, ...rest }) {
  // UNCOMMENT THIS BLOCK WHEN ACTIVATING:
  /*
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <VuiBox
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
      >
        <CircularProgress sx={{ color: "#0075ff" }} />
      </VuiBox>
    );
  }

  return (
    <Route
      {...rest}
      render={(props) =>
        isAuthenticated ? (
          <Component {...props} />
        ) : (
          <Redirect to="/admin-login" />
        )
      }
    />
  );
  */

  // TEMPORARY - Remove when activating
  return null;
}

export default ProtectedRoute;
