import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Box, Button, MenuItem, Select, TextField, Typography
} from "@mui/material";

export default function SearchPage() {
  const navigate = useNavigate();
  const [category, setCategory] = useState<"sdgs"|"targets">("sdgs");
  const [options, setOptions] = useState<string[]>([]);
  const [keywords, setKeywords] = useState("");

  // you could load SDG & target lists from a constants file or endpoint
  const SDGS = ["No Poverty","Zero Hunger", /* … */];
  const TARGETS = ["1.1 Eradicate extreme poverty", /* … */];

  return (
    <Box p={4}>
      <Typography variant="h4">SDG / Target Search</Typography>

      <Select
        value={category}
        onChange={e => {
          setCategory(e.target.value as any);
          setOptions([]);
        }}
        sx={{ mt:2, width: 200 }}
      >
        <MenuItem value="sdgs">SDGs</MenuItem>
        <MenuItem value="targets">Targets</MenuItem>
      </Select>

      <Select
        multiple
        value={options}
        onChange={e => setOptions(e.target.value as string[])}
        sx={{ ml:2, width: 300 }}
        renderValue={selected => selected.join(", ")}
      >
        {(category === "sdgs" ? SDGS : TARGETS).map(opt => (
          <MenuItem key={opt} value={opt}>{opt}</MenuItem>
        ))}
      </Select>

      <TextField
        multiline
        minRows={3}
        placeholder="keywords…"
        fullWidth
        sx={{ mt:3 }}
        value={keywords}
        onChange={e => setKeywords(e.target.value)}
      />

      <Button
        variant="contained"
        sx={{ mt:2 }}
        onClick={() => {
          navigate("/results", {
            state: { category, selections: options, keywords }
          });
        }}
      >
        Search
      </Button>
    </Box>
  );
}
