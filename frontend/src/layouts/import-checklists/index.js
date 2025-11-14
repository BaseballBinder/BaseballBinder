import React, { useState, useEffect, useMemo } from "react";
import axios from "axios";

// Vision UI Dashboard React components
import VuiBox from "components/VuiBox";
import VuiTypography from "components/VuiTypography";
import VuiInput from "components/VuiInput";
import VuiButton from "components/VuiButton";
import VuiAlert from "components/VuiAlert";
import DashboardLayout from "examples/LayoutContainers/DashboardLayout";
import DashboardNavbar from "examples/Navbars/DashboardNavbar";
import Footer from "examples/Footer";
import Card from "@mui/material/Card";
import CircularProgress from "@mui/material/CircularProgress";
import Chip from "@mui/material/Chip";
import Autocomplete from "@mui/material/Autocomplete";
import TextField from "@mui/material/TextField";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";
const DEFAULT_SET_TYPES = [
  "Base",
  "Update",
  "Insert",
  "Autograph",
  "Relic",
  "Memorabilia",
  "Short Print",
  "Super Short Print",
  "Chrome",
  "Parallel",
  "Retail Exclusive",
  "Hobby Exclusive",
  "Rookie Debut",
  "Prospects",
  "Legends",
];

function ImportChecklists() {
  const [year, setYear] = useState("");
  const [productName, setProductName] = useState("");
  const [productExists, setProductExists] = useState(false);
  const [existingTypes, setExistingTypes] = useState([]);

  const [allSetTypes, setAllSetTypes] = useState([]);
  const [typeValue, setTypeValue] = useState("");
  const [typeInputValue, setTypeInputValue] = useState("");
  const [cardCountDeclared, setCardCountDeclared] = useState("");

  const [rawText, setRawText] = useState("");
  const [parsedPreview, setParsedPreview] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);

  const [showTypeField, setShowTypeField] = useState(false);
  const [showTextArea, setShowTextArea] = useState(false);

  const headerCellSx = {
    backgroundColor: "rgba(6, 11, 40, 0.95)",
    color: "#fff",
    fontWeight: "bold",
    border: "1px solid rgba(255, 255, 255, 0.1)",
    textAlign: "left",
  };

  const bodyCellSx = {
    color: "#fff",
    backgroundColor: "rgba(255, 255, 255, 0.03)",
    border: "1px solid rgba(255, 255, 255, 0.05)",
    textAlign: "left",
  };

  const cardColumns = [
    { key: "card_number", label: "Card #", width: "20%", align: "center", render: (item) => item.card_number || "-" },
    { key: "players", label: "Players", width: "30%", align: "left", render: (item) => (item.players || []).join(", ") || "-" },
    { key: "teams", label: "Teams", width: "30%", align: "left", render: (item) => (item.teams || []).join(", ") || "-" },
    { key: "flags", label: "Flags", width: "20%", align: "center", render: (item) => (item.flags || []).join(", ") || "-" },
  ];

  const parallelColumns = [
    { key: "name", label: "Parallel Name", width: "40%", render: (item) => item.name || "-" },
    { key: "print_run", label: "Print Run", width: "15%", render: (item) => (item.print_run ? `/${item.print_run}` : "-") },
    { key: "exclusive", label: "Exclusive", width: "20%", render: (item) => item.exclusive || "-" },
    { key: "notes", label: "Notes", width: "25%", render: (item) => item.notes || "-" },
  ];

  // Fetch all set types when component mounts
  useEffect(() => {
    axios.get(`${API_BASE}/checklists/set-types`)
      .then((res) => {
        setAllSetTypes(res.data.set_types);
      })
      .catch((err) => {
        console.error("Error fetching set types:", err);
      });
  }, []);

  // Check product when year and product name are filled
  useEffect(() => {
    if (year && productName) {
      axios.post(`${API_BASE}/checklists/check-product`, {
        year: parseInt(year),
        product_name: productName
      })
        .then((res) => {
          setProductExists(res.data.exists);
          setExistingTypes(res.data.existing_types);
          setShowTypeField(true);
        })
        .catch((err) => {
          console.error("Error checking product:", err);
          setShowTypeField(true);
        });
    } else {
      setShowTypeField(false);
      setShowTextArea(false);
      setParsedPreview([]);
    }
  }, [year, productName]);

  // Show textarea when type is selected
  useEffect(() => {
    if (typeValue) {
      setShowTextArea(true);
    } else {
      setShowTextArea(false);
      setParsedPreview([]);
    }
  }, [typeValue]);

  const typeOptions = useMemo(() => {
    const merged = new Set([...existingTypes, ...allSetTypes, ...DEFAULT_SET_TYPES]);
    return Array.from(merged)
      .map((label) => (typeof label === "string" ? label.trim() : label))
      .filter(Boolean)
      .sort((a, b) => a.localeCompare(b));
  }, [existingTypes, allSetTypes]);

  const getCurrentType = () => {
    return (typeValue || "").trim();
  };

  const isParallelType = () => {
    const currentType = getCurrentType();
    return currentType ? currentType.toLowerCase().includes("parallel") : false;
  };

  const handleParse = async () => {
    if (!rawText.trim()) {
      setMessage({ type: "error", text: "Please paste checklist text to parse" });
      setParsedPreview([]);
      return;
    }

    setLoading(true);
    setMessage(null);

    try {
      const endpoint = isParallelType() ? "/parallels/parse" : "/checklists/parse";
      const response = await axios.post(`${API_BASE}${endpoint}`, {
        raw_text: rawText,
      });

      if (response.data.length === 0) {
        setMessage({ type: "warning", text: "No cards were parsed. Please check your format." });
        setParsedPreview([]);
      } else {
        setParsedPreview(response.data);
        setMessage({ type: "success", text: `Successfully parsed ${response.data.length} ${isParallelType() ? 'parallels' : 'cards'}` });
      }
    } catch (error) {
      setMessage({ type: "error", text: error.response?.data?.detail || "Failed to parse" });
      setParsedPreview([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (options = {}) => {
    const { keepProduct = false } = options;
    if (!year || !productName || !getCurrentType()) {
      setMessage({ type: "error", text: "Please fill in Year, Product Name, and Type" });
      return;
    }

    if (parsedPreview.length === 0) {
      setMessage({ type: "error", text: "Please parse the checklist first" });
      return;
    }

    setLoading(true);
    setMessage(null);

    try {
      const response = await axios.post(`${API_BASE}/checklists/submit`, {
        year: parseInt(year),
        product_name: productName,
        set_type_name: getCurrentType(),
        submission_type: isParallelType() ? "parallels" : "cards",
        card_count_declared: cardCountDeclared ? parseInt(cardCountDeclared) : null,
        raw_text: rawText,
        parsed_data: parsedPreview,
      });

      const successMessage = keepProduct
        ? `${response.data.message} You can now add another type for ${year} ${productName}.`
        : response.data.message;

      setMessage({
        type: "success",
        text: successMessage
      });

      const nextExistingType = getCurrentType();
      if (nextExistingType) {
        setExistingTypes((prev) =>
          prev.includes(nextExistingType) ? prev : [...prev, nextExistingType]
        );
      }

      if (keepProduct) {
        setTypeValue("");
        setTypeInputValue("");
        setCardCountDeclared("");
        setRawText("");
        setParsedPreview([]);
        setShowTextArea(false);
      } else {
        // Reset entire form
        setYear("");
        setProductName("");
        setTypeValue("");
        setTypeInputValue("");
        setCardCountDeclared("");
        setRawText("");
        setParsedPreview([]);
        setShowTypeField(false);
        setShowTextArea(false);
        setExistingTypes([]);
        setProductExists(false);
      }
    } catch (error) {
      setMessage({ type: "error", text: error.response?.data?.detail || "Failed to submit checklist" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <DashboardLayout>
      <DashboardNavbar />
      <VuiBox py={3}>
        <VuiTypography variant="h3" color="white" fontWeight="bold" mb={3}>
          Import Checklist
        </VuiTypography>

        <Card
          sx={{
            background: 'linear-gradient(127.09deg, rgba(6, 11, 40, 0.94) 19.41%, rgba(10, 14, 35, 0.49) 76.65%)',
            borderRadius: '15px',
            padding: '24px',
          }}
        >
          {/* Instructions */}
          <VuiBox
            mb={3}
            p={2}
            sx={{
              backgroundColor: 'rgba(0, 117, 255, 0.1)',
              borderRadius: '8px',
              border: '1px solid rgba(0, 117, 255, 0.3)'
            }}
          >
            <VuiTypography variant="body2" color="white" fontWeight="bold" mb={1}>
              📋 How to Import a Checklist
            </VuiTypography>
            <VuiTypography variant="caption" color="text" component="div">
              <strong>Step 1:</strong> Enter the Year and Product Name below<br />
              <strong>Step 2:</strong> Select the Type (Base, Insert, Autograph, etc.) or create a custom type<br />
              <strong>Step 3:</strong> Paste your checklist text in Beckett/TCDB format<br />
              <strong>Step 4:</strong> Preview and submit for admin review
            </VuiTypography>
          </VuiBox>

          {message && (
            <VuiAlert color={message.type} sx={{ mb: 3 }}>
              {message.text}
            </VuiAlert>
          )}

          {/* Step 1: Year & Product Name */}
          <VuiBox sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2, mb: 3 }}>
            <VuiBox>
              <VuiTypography variant="caption" color="white" fontWeight="bold" mb={1}>
                Year *
              </VuiTypography>
              <VuiInput
                placeholder="e.g., 2024"
                value={year}
                onChange={(e) => setYear(e.target.value)}
                sx={{ width: '100%' }}
              />
            </VuiBox>

            <VuiBox>
              <VuiTypography variant="caption" color="white" fontWeight="bold" mb={1}>
                Product Name *
              </VuiTypography>
              <VuiInput
                placeholder="e.g., Topps Series 1"
                value={productName}
                onChange={(e) => setProductName(e.target.value)}
                sx={{ width: '100%' }}
              />
            </VuiBox>
          </VuiBox>

          {/* Product Status Info */}
          {showTypeField && (
            <VuiBox mb={3}>
              {productExists ? (
                <VuiBox sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <VuiTypography variant="body2" color="success">
                    ✓ Product exists
                  </VuiTypography>
                  {existingTypes.length > 0 && (
                    <>
                      <VuiTypography variant="body2" color="text">
                        | Existing types:
                      </VuiTypography>
                      {existingTypes.map((type, idx) => (
                        <Chip
                          key={idx}
                          label={type}
                          size="small"
                          sx={{
                            backgroundColor: 'rgba(0, 117, 255, 0.2)',
                            color: '#0075ff',
                            fontSize: '0.75rem'
                          }}
                        />
                      ))}
                    </>
                  )}
                </VuiBox>
              ) : (
                <VuiTypography variant="body2" color="warning" mb={2}>
                  ⓘ New product - will be created upon approval
                </VuiTypography>
              )}

              {/* Step 2: Type Selection */}
              <VuiBox>
                <VuiTypography variant="caption" color="white" fontWeight="bold" mb={1}>
                  Type *
                </VuiTypography>

                <Autocomplete
                  freeSolo
                  options={typeOptions}
                  value={typeValue}
                  inputValue={typeInputValue}
                  onChange={(_, newValue) => {
                    const next = (newValue || "").trim();
                    setTypeValue(next);
                    setTypeInputValue(next);
                  }}
                  onInputChange={(_, newInputValue) => setTypeInputValue(newInputValue)}
                  ListboxProps={{
                    sx: {
                      backgroundColor: "rgba(6,11,40,0.95)",
                      color: "#fff",
                    },
                  }}
                  sx={{
                    "& .MuiOutlinedInput-root": {
                      backgroundColor: "rgba(6,11,40,0.85)",
                      borderRadius: "12px",
                      border: "1px solid rgba(226,232,240,0.3)",
                      color: "#fff",
                      paddingRight: "40px",
                    },
                    "& .MuiOutlinedInput-root:hover .MuiOutlinedInput-notchedOutline": {
                      borderColor: "rgba(226,232,240,0.6)",
                    },
                    "& .MuiOutlinedInput-root.Mui-focused": {
                      borderColor: "#0075ff",
                      boxShadow: "0 0 0 1px rgba(0,117,255,0.4)",
                    },
                    "& .MuiOutlinedInput-notchedOutline": {
                      border: "1px solid rgba(226,232,240,0.3)",
                    },
                    "& .MuiInputBase-input": {
                      color: "#fff",
                    },
                    "& .MuiSvgIcon-root": {
                      color: "#fff",
                    },
                  }}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      placeholder="Start typing a type (e.g., Base, Insert, Relic)"
                      variant="outlined"
                      InputProps={{
                        ...params.InputProps,
                        style: {
                          color: "#fff",
                          padding: "4px 10px",
                        },
                      }}
                    />
                  )}
                />
              </VuiBox>

              {/* Card Count Declared */}
              <VuiBox mt={2}>
                <VuiTypography variant="caption" color="white" fontWeight="bold" mb={1}>
                  Expected Card Count (Optional)
                </VuiTypography>
                <VuiTypography variant="caption" color="text" mb={1} display="block">
                  How many {isParallelType() ? 'parallels' : 'cards'} should exist in this {getCurrentType()} set?
                </VuiTypography>
                <VuiInput
                  type="number"
                  placeholder="e.g., 330"
                  value={cardCountDeclared}
                  onChange={(e) => setCardCountDeclared(e.target.value)}
                  sx={{ width: '200px' }}
                />
              </VuiBox>
            </VuiBox>
          )}

          {/* Step 3: Paste Checklist */}
          {showTextArea && (
            <>
              <VuiBox mb={2}>
                <VuiTypography variant="caption" color="white" fontWeight="bold" mb={1}>
                  Paste Checklist Text (Beckett/TCDB format)
                </VuiTypography>
                <textarea
                  placeholder={isParallelType()
                    ? "Example:\nGold /50\nRainbow Foil /25 (Hobby exclusive)\nBlack /1"
                    : "Example:\n1 Shohei Ohtani - Angels RC\n2 Aaron Judge - Yankees\n3 Mike Trout - Angels SP"
                  }
                  value={rawText}
                  onChange={(e) => setRawText(e.target.value)}
                  rows={10}
                  style={{
                    width: '100%',
                    padding: '12px',
                    borderRadius: '8px',
                    backgroundColor: 'rgba(0, 0, 0, 0.3)',
                    border: '1px solid rgba(255, 255, 255, 0.2)',
                    color: '#fff',
                    fontFamily: 'monospace',
                    fontSize: '14px',
                    resize: 'vertical',
                  }}
                />
              </VuiBox>

              <VuiBox sx={{ display: 'flex', gap: 2, mb: 3 }}>
                <VuiButton
                  variant="contained"
                  color="info"
                  onClick={handleParse}
                  disabled={loading}
                >
                  {loading ? <CircularProgress size={20} color="inherit" /> : "Parse Preview"}
                </VuiButton>

                <VuiButton
                  variant="contained"
                  color="success"
                  onClick={() => handleSubmit({ keepProduct: false })}
                  disabled={loading || parsedPreview.length === 0}
                >
                  {loading ? <CircularProgress size={20} color="inherit" /> : "Submit for Admin Review"}
                </VuiButton>
                <VuiButton
                  variant="contained"
                  color="warning"
                  onClick={() => handleSubmit({ keepProduct: true })}
                  disabled={loading || parsedPreview.length === 0}
                >
                  {loading ? <CircularProgress size={20} color="inherit" /> : "Submit & Add Another Type"}
                </VuiButton>
              </VuiBox>

              {/* Preview Table */}
              {parsedPreview.length > 0 && (
                <VuiBox>
                  <VuiTypography variant="h6" color="white" mb={2}>
                    Parsed Preview ({parsedPreview.length} {isParallelType() ? "parallels" : "cards"})
                  </VuiTypography>
                  <VuiBox
                    sx={{
                      borderRadius: "15px",
                      border: "1px solid rgba(255,255,255,0.1)",
                      background: "linear-gradient(135deg, rgba(6,11,40,0.95), rgba(10,14,35,0.6))",
                      boxShadow: "0 20px 35px rgba(0,0,0,0.4)",
                      overflow: "hidden",
                    }}
                  >
                    {(() => {
                      const columns = isParallelType() ? parallelColumns : cardColumns;
                      const template = columns.map((col) => col.width).join(" ");
                      return (
                        <>
                          <VuiBox
                            sx={{
                              display: "grid",
                              gridTemplateColumns: template,
                              backgroundColor: "rgba(6,11,40,0.97)",
                              borderBottom: "1px solid rgba(255,255,255,0.18)",
                              px: 3,
                              py: 1.5,
                            }}
                          >
                            {columns.map((col) => (
                              <VuiTypography
                                key={col.key}
                                variant="caption"
                                color="white"
                                fontWeight="bold"
                                sx={{
                                  textTransform: "uppercase",
                                  letterSpacing: "0.8px",
                                  textAlign: col.align || "left",
                                }}
                              >
                                {col.label}
                              </VuiTypography>
                            ))}
                          </VuiBox>

                          <VuiBox
                            sx={{
                              maxHeight: 400,
                              overflowY: "auto",
                            }}
                          >
                            {parsedPreview.map((item, idx) => (
                              <VuiBox
                                key={`${item.card_number || item.name}-${idx}`}
                                sx={{
                                  display: "grid",
                                  gridTemplateColumns: template,
                                  px: 3,
                                  py: 1.25,
                                  backgroundColor:
                                    idx % 2 === 0 ? "rgba(255,255,255,0.04)" : "rgba(255,255,255,0.08)",
                                  borderBottom: "1px solid rgba(255,255,255,0.06)",
                                }}
                              >
                                {columns.map((col) => (
                                  <VuiTypography
                                    key={col.key}
                                    variant="button"
                                    color="white"
                                    fontWeight="regular"
                                    sx={{ textAlign: col.align || "left", fontSize: "14px" }}
                                  >
                                    {col.render(item)}
                                  </VuiTypography>
                                ))}
                              </VuiBox>
                            ))}
                          </VuiBox>
                        </>
                      );
                    })()}
                  </VuiBox>
                </VuiBox>
              )}
            </>
          )}
        </Card>
      </VuiBox>
      <Footer />
    </DashboardLayout>
  );
}

export default ImportChecklists;
