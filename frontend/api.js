import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000", // FastAPI backend
});

// Example endpoints
export const getChecklist = () => api.get("/checklist");
export const getEbayItems = () => api.get("/ebay/search-history");
