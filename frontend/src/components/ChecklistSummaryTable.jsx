import React, { useEffect, useState } from "react";
import { Table, TableBody, TableCell, TableHead, TableRow, CircularProgress, TableContainer } from "@mui/material";
import axios from "axios";
import VuiBox from "components/VuiBox";
import VuiTypography from "components/VuiTypography";
import VuiAlert from "components/VuiAlert";

export default function ChecklistSummaryTable({ refreshTrigger }) {
  const [checklists, setChecklists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchChecklists = async () => {
    setLoading(true);
    setError(null);

    try {
      const res = await axios.get("http://127.0.0.1:8000/checklist/summary");
      console.log("📦 Checklists loaded:", res.data);
      setChecklists(res.data || []);
    } catch (err) {
      console.error("❌ Error loading checklists:", err);
      setError("Failed to load checklists. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchChecklists();
  }, [refreshTrigger]); // Refresh when refreshTrigger changes

  // Columns configuration to drive header/body consistently
  const columns = [
    { key: 'set_name',   label: 'Set Name',   width: '50%', align: 'left' },
    { key: 'year',       label: 'Year',       width: '25%', align: 'left' },
    { key: 'card_count', label: 'Card Count', width: '25%', align: 'right' },
  ];

  if (loading) {
    return (
      <VuiBox
        sx={{
          background: 'linear-gradient(127.09deg, rgba(6, 11, 40, 0.94) 19.41%, rgba(10, 14, 35, 0.49) 76.65%)',
          borderRadius: '15px',
          padding: '40px',
          textAlign: 'center',
        }}
      >
        <CircularProgress sx={{ color: "#0075ff" }} size={40} />
        <VuiTypography variant="body2" color="text" mt={2}>
          Loading checklists...
        </VuiTypography>
      </VuiBox>
    );
  }

  if (error) {
    return (
      <VuiBox mb={3}>
        <VuiAlert color="error">{error}</VuiAlert>
      </VuiBox>
    );
  }

  return (
    <VuiBox>
      {/* Statistics Card */}
      <VuiBox mb={3}>
        <VuiBox
          sx={{
            background: 'linear-gradient(127.09deg, rgba(6, 11, 40, 0.94) 19.41%, rgba(10, 14, 35, 0.49) 76.65%)',
            borderRadius: '15px',
            padding: '20px',
            boxShadow: '0px 3.5px 5.5px rgba(0, 0, 0, 0.02)',
          }}
        >
          <VuiBox display="flex" justifyContent="space-between" alignItems="center">
            <VuiBox>
              <VuiTypography variant="caption" color="text" textTransform="uppercase">
                Total Checklists
              </VuiTypography>
              <VuiTypography variant="h2" color="white" fontWeight="bold">
                {checklists.length}
              </VuiTypography>
            </VuiBox>
            <VuiBox>
              <VuiTypography variant="caption" color="text" textTransform="uppercase">
                Total Cards
              </VuiTypography>
              <VuiTypography variant="h2" color="white" fontWeight="bold">
                {checklists.reduce((sum, cl) => sum + (cl.card_count || 0), 0).toLocaleString()}
              </VuiTypography>
            </VuiBox>
          </VuiBox>
        </VuiBox>
      </VuiBox>

      {/* Checklists Table */}
      <VuiBox
        sx={{
          background: 'linear-gradient(127.09deg, rgba(6, 11, 40, 0.94) 19.41%, rgba(10, 14, 35, 0.49) 76.65%)',
          borderRadius: '15px',
          padding: '20px',
          boxShadow: '0px 3.5px 5.5px rgba(0, 0, 0, 0.02)',
        }}
      >
        {/* CSS Grid header */}
        <VuiBox sx={{ display: 'grid', gridTemplateColumns: '50% 25% 25%', alignItems: 'center', px: 2, py: 1.5, borderBottom: '1px solid rgba(226, 232, 240, 0.1)' }}>
          <VuiTypography variant="caption" color="white" sx={{ textTransform: 'uppercase', fontWeight: 'bold', fontSize: '12px' }}>Set Name</VuiTypography>
          <VuiTypography variant="caption" color="white" sx={{ textTransform: 'uppercase', fontWeight: 'bold', fontSize: '12px' }}>Year</VuiTypography>
          <VuiTypography variant="caption" color="white" sx={{ textTransform: 'uppercase', fontWeight: 'bold', fontSize: '12px', textAlign: 'right' }}>Card Count</VuiTypography>
        </VuiBox>
        {/* CSS Grid body */}
        {checklists.length > 0 ? (
          checklists.map((cl, i) => (
            <VuiBox key={i} sx={{ display: 'grid', gridTemplateColumns: '50% 25% 25%', alignItems: 'center', py: 1.5, borderBottom: '1px solid rgba(226, 232, 240, 0.1)' }}>
              <VuiTypography variant="button" color="white" fontWeight="medium">{cl.set_name}</VuiTypography>
              <VuiTypography variant="button" color="text">{cl.year}</VuiTypography>
              <VuiTypography variant="button" color="white" fontWeight="medium" sx={{ textAlign: 'right' }}>{cl.card_count.toLocaleString()}</VuiTypography>
            </VuiBox>
          ))
        ) : (
          <VuiBox sx={{ textAlign: 'center', py: 3 }}>
            <VuiTypography variant="body2" color="text" py={3}>
              No checklists found. Click "Rescan Folder" to import checklists.
            </VuiTypography>
          </VuiBox>
        )}
      </VuiBox>
    </VuiBox>
  );
}
