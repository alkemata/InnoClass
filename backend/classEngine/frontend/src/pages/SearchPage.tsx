// src/SearchPage.tsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  OutlinedInput,
  Box,
  Chip,
  TextField,
  Button,
} from '@mui/material';
import { SelectChangeEvent } from '@mui/material/Select'; // Import SelectChangeEvent

import sdgsData from '../data/sdgs.json'; // Import JSON data
import Link from '@mui/material/Link';

// Define the type for the SDG data for better type safety
interface SdgsDataType {
  [key: string]: string;
}

const typedSdgsData: SdgsDataType = sdgsData; // Type assertion

const ITEM_HEIGHT = 48;
const ITEM_PADDING_TOP = 8;
const MenuProps = {
  PaperProps: {
    style: {
      maxHeight: ITEM_HEIGHT * 4.5 + ITEM_PADDING_TOP,
      width: 250,
    },
  },
};

function SearchPage() {
  const [selectedSdgs, setSelectedSdgs] = useState<string[]>([]);
  const [keywords, setKeywords] = useState<string>('');
  const navigate = useNavigate();

  const handleSdgChange = (event: SelectChangeEvent<string[]>) => {
    const {
      target: { value },
    } = event;
    // On autofill we get a stringified value.
    setSelectedSdgs(typeof value === 'string' ? value.split(',') : value);
  };

  const handleKeywordsChange = (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setKeywords(event.target.value);
  };

  const handleSearch = () => {
    const sdgIds = selectedSdgs.join(',');
    const keywordList = keywords.split(',').map(kw => kw.trim()).filter(kw => kw !== '');
    const keywordsQuery = keywordList.join('&keywords=');

    navigate(`/results?sdg_ids=${sdgIds}&keywords=${keywordsQuery}`);
  };

  // Map the sdgsData to an array of objects for easier iteration
  const sdgOptions = Object.entries(typedSdgsData).map(([id, title]) => ({
    id,
    title,
  }));

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          InnoClass
          <Link href="/Menu" color="inherit" underline="none" sx={{ ml: 2 }}> {/* Add the Link component */}
            Menu
          </Link>
        </Typography>
      </Toolbar>
    </AppBar>

      <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
        <Typography variant="h4" component="h2" gutterBottom>
          Search SDGs
        </Typography>

        <FormControl fullWidth sx={{ mb: 3 }}>
          <InputLabel id="sdg-multiple-chip-label">Select SDGs</InputLabel>
          <Select<string[]> // Explicitly type the Select component
            labelId="sdg-multiple-chip-label"
            id="sdg-multiple-chip"
            multiple
            value={selectedSdgs}
            onChange={handleSdgChange}
            input={<OutlinedInput id="select-multiple-chip" label="Select SDGs" />}
            renderValue={(selected) => (
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {selected.map((value) => (
                  <Chip key={value} label={typedSdgsData[value]} />
                ))}
              </Box>
            )}
            MenuProps={MenuProps}
          >
            {sdgOptions.map((sdg) => (
              <MenuItem
                key={sdg.id}
                value={sdg.id}
              >
                {sdg.title}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <TextField
          fullWidth
          multiline
          rows={4}
          label="Enter Keywords (comma-separated)"
          value={keywords}
          onChange={handleKeywordsChange}
          variant="outlined"
          sx={{ mb: 3 }}
        />

        <Button
          variant="contained"
          onClick={handleSearch}
          sx={{ py: 1.5, px: 4 }}
        >
          Search
        </Button>
      </Container>
    </Box>
  );
}

export default SearchPage;