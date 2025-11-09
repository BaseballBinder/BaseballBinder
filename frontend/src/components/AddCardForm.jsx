import React, { useState } from "react";
import axios from "axios";
import { Grid, Checkbox, FormControlLabel } from "@mui/material";
import VuiBox from "components/VuiBox";
import VuiTypography from "components/VuiTypography";
import VuiInput from "components/VuiInput";
import VuiButton from "components/VuiButton";
import VuiAlert from "components/VuiAlert";

export default function AddCardForm() {
  const [formData, setFormData] = useState({
    set_name: "",
    card_number: "",
    player: "",
    team: "",
    year: "",
    variety: "",
    parallel: "",
    autograph: false,
    numbered: "",
    graded: "",
    price_paid: "",
    current_value: "",
    sold_price: "",
    location: "",
    notes: "",
    quantity: "1",
  });

  const [loading, setLoading] = useState(false);
  const [alert, setAlert] = useState({ show: false, type: "", message: "" });

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setAlert({ show: false, type: "", message: "" });

    try {
      // Convert numeric fields
      const submitData = {
        ...formData,
        price_paid: formData.price_paid ? parseFloat(formData.price_paid) : null,
        current_value: formData.current_value ? parseFloat(formData.current_value) : null,
        sold_price: formData.sold_price ? parseFloat(formData.sold_price) : null,
        quantity: parseInt(formData.quantity) || 1,
      };

      // Remove empty strings
      Object.keys(submitData).forEach(key => {
        if (submitData[key] === "") {
          submitData[key] = null;
        }
      });

      await axios.post("http://127.0.0.1:8000/cards/", submitData);

      setAlert({
        show: true,
        type: "success",
        message: "Card added successfully!",
      });

      // Reset form
      setFormData({
        set_name: "",
        card_number: "",
        player: "",
        team: "",
        year: "",
        variety: "",
        parallel: "",
        autograph: false,
        numbered: "",
        graded: "",
        price_paid: "",
        current_value: "",
        sold_price: "",
        location: "",
        notes: "",
        quantity: "1",
      });

      // Auto-hide success message
      setTimeout(() => {
        setAlert({ show: false, type: "", message: "" });
      }, 3000);
    } catch (err) {
      console.error("❌ Error adding card:", err);
      setAlert({
        show: true,
        type: "error",
        message: err.response?.data?.detail || "Failed to add card. Please try again.",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <VuiBox
      component="form"
      onSubmit={handleSubmit}
      sx={{
        background: 'linear-gradient(127.09deg, rgba(6, 11, 40, 0.94) 19.41%, rgba(10, 14, 35, 0.49) 76.65%)',
        borderRadius: '15px',
        padding: '40px',
        boxShadow: '0px 3.5px 5.5px rgba(0, 0, 0, 0.02)',
      }}
    >
      <VuiBox mb={3}>
        <VuiTypography variant="h4" color="white" fontWeight="bold" mb={1}>
          Add New Card
        </VuiTypography>
        <VuiTypography variant="body2" color="text">
          Add a baseball card to your collection
        </VuiTypography>
      </VuiBox>

      {alert.show && (
        <VuiBox mb={3}>
          <VuiAlert color={alert.type === "success" ? "success" : "error"}>
            {alert.message}
          </VuiAlert>
        </VuiBox>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <VuiBox mb={2}>
            <VuiTypography variant="caption" color="white" fontWeight="bold" mb={1}>
              Set Name
            </VuiTypography>
            <VuiInput
              name="set_name"
              placeholder="e.g., 2024 Topps Chrome"
              value={formData.set_name}
              onChange={handleChange}
              fullWidth
            />
          </VuiBox>
        </Grid>

        <Grid item xs={12} md={6}>
          <VuiBox mb={2}>
            <VuiTypography variant="caption" color="white" fontWeight="bold" mb={1}>
              Card Number
            </VuiTypography>
            <VuiInput
              name="card_number"
              placeholder="e.g., 1, RC-1, etc."
              value={formData.card_number}
              onChange={handleChange}
              fullWidth
            />
          </VuiBox>
        </Grid>

        <Grid item xs={12} md={6}>
          <VuiBox mb={2}>
            <VuiTypography variant="caption" color="white" fontWeight="bold" mb={1}>
              Player Name
            </VuiTypography>
            <VuiInput
              name="player"
              placeholder="e.g., Mike Trout"
              value={formData.player}
              onChange={handleChange}
              fullWidth
            />
          </VuiBox>
        </Grid>

        <Grid item xs={12} md={6}>
          <VuiBox mb={2}>
            <VuiTypography variant="caption" color="white" fontWeight="bold" mb={1}>
              Team
            </VuiTypography>
            <VuiInput
              name="team"
              placeholder="e.g., Los Angeles Angels"
              value={formData.team}
              onChange={handleChange}
              fullWidth
            />
          </VuiBox>
        </Grid>

        <Grid item xs={12} md={4}>
          <VuiBox mb={2}>
            <VuiTypography variant="caption" color="white" fontWeight="bold" mb={1}>
              Year
            </VuiTypography>
            <VuiInput
              name="year"
              placeholder="e.g., 2024"
              value={formData.year}
              onChange={handleChange}
              fullWidth
            />
          </VuiBox>
        </Grid>

        <Grid item xs={12} md={4}>
          <VuiBox mb={2}>
            <VuiTypography variant="caption" color="white" fontWeight="bold" mb={1}>
              Variety
            </VuiTypography>
            <VuiInput
              name="variety"
              placeholder="e.g., Base, Refractor"
              value={formData.variety}
              onChange={handleChange}
              fullWidth
            />
          </VuiBox>
        </Grid>

        <Grid item xs={12} md={4}>
          <VuiBox mb={2}>
            <VuiTypography variant="caption" color="white" fontWeight="bold" mb={1}>
              Parallel
            </VuiTypography>
            <VuiInput
              name="parallel"
              placeholder="e.g., Gold, Red"
              value={formData.parallel}
              onChange={handleChange}
              fullWidth
            />
          </VuiBox>
        </Grid>

        <Grid item xs={12} md={4}>
          <VuiBox mb={2}>
            <VuiTypography variant="caption" color="white" fontWeight="bold" mb={1}>
              Numbered
            </VuiTypography>
            <VuiInput
              name="numbered"
              placeholder="e.g., 5/10, 25/99"
              value={formData.numbered}
              onChange={handleChange}
              fullWidth
            />
          </VuiBox>
        </Grid>

        <Grid item xs={12} md={4}>
          <VuiBox mb={2}>
            <VuiTypography variant="caption" color="white" fontWeight="bold" mb={1}>
              Graded
            </VuiTypography>
            <VuiInput
              name="graded"
              placeholder="e.g., PSA 10, BGS 9.5"
              value={formData.graded}
              onChange={handleChange}
              fullWidth
            />
          </VuiBox>
        </Grid>

        <Grid item xs={12} md={4}>
          <VuiBox mb={2}>
            <VuiTypography variant="caption" color="white" fontWeight="bold" mb={1}>
              Quantity
            </VuiTypography>
            <VuiInput
              name="quantity"
              type="number"
              placeholder="1"
              value={formData.quantity}
              onChange={handleChange}
              fullWidth
            />
          </VuiBox>
        </Grid>

        <Grid item xs={12} md={4}>
          <VuiBox mb={2}>
            <VuiTypography variant="caption" color="white" fontWeight="bold" mb={1}>
              Price Paid ($)
            </VuiTypography>
            <VuiInput
              name="price_paid"
              type="number"
              step="0.01"
              placeholder="e.g., 25.00"
              value={formData.price_paid}
              onChange={handleChange}
              fullWidth
            />
          </VuiBox>
        </Grid>

        <Grid item xs={12} md={4}>
          <VuiBox mb={2}>
            <VuiTypography variant="caption" color="white" fontWeight="bold" mb={1}>
              Current Value ($)
            </VuiTypography>
            <VuiInput
              name="current_value"
              type="number"
              step="0.01"
              placeholder="e.g., 50.00"
              value={formData.current_value}
              onChange={handleChange}
              fullWidth
            />
          </VuiBox>
        </Grid>

        <Grid item xs={12} md={4}>
          <VuiBox mb={2}>
            <VuiTypography variant="caption" color="white" fontWeight="bold" mb={1}>
              Sold Price ($)
            </VuiTypography>
            <VuiInput
              name="sold_price"
              type="number"
              step="0.01"
              placeholder="e.g., 45.00"
              value={formData.sold_price}
              onChange={handleChange}
              fullWidth
            />
          </VuiBox>
        </Grid>

        <Grid item xs={12} md={6}>
          <VuiBox mb={2}>
            <VuiTypography variant="caption" color="white" fontWeight="bold" mb={1}>
              Location
            </VuiTypography>
            <VuiInput
              name="location"
              placeholder="e.g., Binder 1, Page 5"
              value={formData.location}
              onChange={handleChange}
              fullWidth
            />
          </VuiBox>
        </Grid>

        <Grid item xs={12} md={6}>
          <VuiBox mb={2} display="flex" alignItems="center" height="100%">
            <FormControlLabel
              control={
                <Checkbox
                  name="autograph"
                  checked={formData.autograph}
                  onChange={handleChange}
                  sx={{
                    color: "#0075ff",
                    '&.Mui-checked': {
                      color: "#0075ff",
                    },
                  }}
                />
              }
              label={
                <VuiTypography variant="caption" color="white" fontWeight="bold">
                  Autograph
                </VuiTypography>
              }
            />
          </VuiBox>
        </Grid>

        <Grid item xs={12}>
          <VuiBox mb={2}>
            <VuiTypography variant="caption" color="white" fontWeight="bold" mb={1}>
              Notes
            </VuiTypography>
            <VuiInput
              name="notes"
              placeholder="Additional notes about this card..."
              value={formData.notes}
              onChange={handleChange}
              multiline
              rows={3}
              fullWidth
            />
          </VuiBox>
        </Grid>

        <Grid item xs={12}>
          <VuiBox mt={2}>
            <VuiButton
              type="submit"
              color="info"
              variant="contained"
              fullWidth
              disabled={loading}
              sx={{ height: "44px" }}
            >
              {loading ? "Adding..." : "Add Card"}
            </VuiButton>
          </VuiBox>
        </Grid>
      </Grid>
    </VuiBox>
  );
}
