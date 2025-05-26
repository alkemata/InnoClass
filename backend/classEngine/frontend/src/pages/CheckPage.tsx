import React, { useState, useEffect } from 'react';
import {
  Typography,
  Box,
  Table,
  TableContainer,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  Checkbox,
  Paper,
  FormControlLabel,
  Button, // Added Button
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton, // Added IconButton
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack'; // Added ArrowBackIcon
import ArrowForwardIcon from '@mui/icons-material/ArrowForward'; // Added ArrowForwardIcon
import { AxiosError } from 'axios';
import api from '../api';
import sdgsData from '../data/sdgs.json';

interface EntryData {
  id: string;
  title: string;
  cleaned_text: string;
  sdg: Array<{ value: string; score: number }>; // Updated sdg type
  target: string[]; // Assuming target might also need this structure later
  valid: boolean;
  reference: boolean;
}

// Define the new paginated response interface
interface PaginatedCheckPageDataResponse {
  entry: EntryData | null;
  total: number;
  offset: number;
}

interface SdgDefinition {
  [key: string]: string;
}

const sdgs: SdgDefinition = sdgsData;

const CheckPage: React.FC = () => {
  const [entry, setEntry] = useState<EntryData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSdgs, setSelectedSdgs] = useState<Array<{ value: string; score: number }>>([]);
  const [updatingSdgs, setUpdatingSdgs] = useState<boolean>(false);
  const [sdgUpdateError, setSdgUpdateError] = useState<string | null>(null);
  const [updatingValidation, setUpdatingValidation] = useState<boolean>(false);
  const [validationUpdateError, setValidationUpdateError] = useState<string | null>(null);
  const [updatingReference, setUpdatingReference] = useState<boolean>(false);
  const [referenceUpdateError, setReferenceUpdateError] = useState<string | null>(null);
  const [validationFilter, setValidationFilter] = useState<string>("false");
  const [referenceFilter, setReferenceFilter] = useState<string>("all");
  
  // New state variables for pagination
  const [currentPage, setCurrentPage] = useState<number>(0); // 0-indexed
  const [totalEntries, setTotalEntries] = useState<number>(0);

  const fetchEntry = async (requestedPage: number) => {
    try {
      setLoading(true);
      setError(null);
      // Do not clear entry immediately to allow smoother transition if only total/offset updates
      // setEntry(null); 

      let queryParams = [`offset=${requestedPage}`];
      if (validationFilter !== "all") {
        queryParams.push(`filter_validation=${validationFilter}`);
      }
      if (referenceFilter !== "all") {
        queryParams.push(`filter_reference=${referenceFilter}`);
      }
      const queryString = queryParams.length > 0 ? `?${queryParams.join('&')}` : '';
      
      const response = await api.get<PaginatedCheckPageDataResponse>(`/check/entry${queryString}`);
      
      setEntry(response.data.entry);
      setSelectedSdgs(response.data.entry?.sdg || []);
      setTotalEntries(response.data.total);
      setCurrentPage(response.data.offset); // The backend returns the offset it used

      if (!response.data.entry && response.data.total > 0 && requestedPage < response.data.total) {
        // This case might indicate an issue or simply that the specific offset didn't return an entry
        // but there are entries in total. Could be an error or just end of a specific filtered list.
        setError('No entry found at this specific page, though matching entries exist.');
      } else if (!response.data.entry && response.data.total === 0) {
        setError('No entries found matching your filter criteria.');
      }

      setLoading(false);
    } catch (err) {
      const axiosError = err as AxiosError;
      if (axiosError.isAxiosError && axiosError.response?.status === 404) {
        // This 404 from the backend's perspective usually means the endpoint itself wasn't found,
        // or a document ID in an update operation was not found.
        // For fetching, a 404 might be less common if the backend handles "no results" with an empty entry list.
        // The logic above (response.data.entry being null) is preferred for "no results".
        setError('Error fetching data (404). The requested resource was not found.');
      } else {
        setError('Failed to fetch data. Please try again later.');
        console.error("Fetch error:", err);
      }
      setLoading(false);
      // setEntry(null); // Clear entry on error to avoid displaying stale data
    }
  };
  
  useEffect(() => {
    fetchEntry(0); // Initial fetch for the first page (offset 0)
  }, []); // Keep dependency array minimal for initial load

  const handleSdgChange = async (sdgKey: string, isChecked: boolean) => {
    if (!entry || !entry.id) {
      console.error("No entry loaded or entry ID is missing. Cannot update SDGs.");
      setSdgUpdateError("Cannot update SDGs: No active entry.");
      return;
    }

    let newSelectedSdgs: Array<{ value: string; score: number }>;
    if (isChecked) {
      newSelectedSdgs = [...selectedSdgs, { value: sdgKey, score: 1 }]; // Add new structure with default score 1
    } else {
      newSelectedSdgs = selectedSdgs.filter(s => s.value !== sdgKey); // Filter by value property
    }

    setSelectedSdgs(newSelectedSdgs); // Optimistic update

    setUpdatingSdgs(true);
    setSdgUpdateError(null);

    try {
      await api.put(`/check/update_sdgs`, {
        doc_id: entry.id,
        sdgs: newSelectedSdgs,
      });
      // Optionally, handle success (e.g., temporary success message)
    } catch (err) {
      console.error("Failed to update SDGs:", err);
      setSdgUpdateError("Failed to update SDGs. Please try again.");
      // Optionally, revert selectedSdgs here if desired, e.g.:
      // setSelectedSdgs(selectedSdgs); // Reverts to state before this change
    } finally {
      setUpdatingSdgs(false);
    }
  };

  const handleValidationChange = async (isChecked: boolean) => {
    if (!entry || !entry.id) {
      console.error("No entry loaded or entry ID is missing. Cannot update validation status.");
      setValidationUpdateError("Cannot update validation status: No active entry.");
      return;
    }

    const originalValidStatus = entry.valid;
    setEntry(prevEntry => prevEntry ? { ...prevEntry, valid: isChecked } : null); // Optimistic update

    setUpdatingValidation(true);
    setValidationUpdateError(null);

    try {
      await api.put(`/check/update_validation`, {
        doc_id: entry.id,
        valid: isChecked,
      });
      // Success: Optimistic update is now confirmed
    } catch (err) {
      console.error("Failed to update validation status:", err);
      setValidationUpdateError("Failed to update validation status. Please try again.");
      setEntry(prevEntry => prevEntry ? { ...prevEntry, valid: originalValidStatus } : null); // Revert
    } finally {
      setUpdatingValidation(false);
    }
  };

  const handleReferenceChange = async (isChecked: boolean) => {
    if (!entry || !entry.id) {
      console.error("No entry loaded or entry ID is missing. Cannot update reference status.");
      setReferenceUpdateError("Cannot update reference status: No active entry.");
      return;
    }

    const originalReferenceStatus = entry.reference;
    setEntry(prevEntry => prevEntry ? { ...prevEntry, reference: isChecked } : null); // Optimistic update

    setUpdatingReference(true);
    setReferenceUpdateError(null);

    try {
      await api.put(`/check/update_reference`, { // Ensure this endpoint exists and is correct
        doc_id: entry.id,
        reference: isChecked,
      });
      // Success: Optimistic update is now confirmed
    } catch (err) {
      console.error("Failed to update reference status:", err);
      setReferenceUpdateError("Failed to update reference status. Please try again.");
      setEntry(prevEntry => prevEntry ? { ...prevEntry, reference: originalReferenceStatus } : null); // Revert
    } finally {
      setUpdatingReference(false);
    }
  };
  
  if (loading && !entry && totalEntries === 0) { // Show initial loading message only if no entry and no total known
    return <Typography>Loading...</Typography>;
  }
  
  return (
    <Box sx={{ p: 2 }}>
      {/* Filter and Navigation Controls */}
      <Box sx={{ display: 'flex', gap: 2, mb: 2, alignItems: 'center', flexWrap: 'wrap' }}>
        <FormControl size="small" sx={{ minWidth: 180 }}>
          <InputLabel id="validation-filter-label">Filter by Validation</InputLabel>
          <Select
            labelId="validation-filter-label"
            value={validationFilter}
            label="Filter by Validation"
            onChange={(e) => setValidationFilter(e.target.value)}
          >
            <MenuItem value="all">Show All</MenuItem>
            <MenuItem value="false">Not Validated</MenuItem>
            <MenuItem value="true">Validated</MenuItem>
          </Select>
        </FormControl>

        <FormControl size="small" sx={{ minWidth: 180 }}>
          <InputLabel id="reference-filter-label">Filter by Reference</InputLabel>
          <Select
            labelId="reference-filter-label"
            value={referenceFilter}
            label="Filter by Reference"
            onChange={(e) => setReferenceFilter(e.target.value)}
          >
            <MenuItem value="all">Show All</MenuItem>
            <MenuItem value="false">Not Reference</MenuItem>
            <MenuItem value="true">Reference</MenuItem>
          </Select>
        </FormControl>
        <Button variant="contained" onClick={() => fetchEntry(0)} disabled={loading}>
          {loading ? 'Fetching...' : 'Apply Filters & Fetch First'}
        </Button>
        <IconButton onClick={() => fetchEntry(currentPage - 1)} disabled={currentPage <= 0 || loading}>
          <ArrowBackIcon />
        </IconButton>
        <Typography sx={{ minWidth: 100, textAlign: 'center' }}>
          {totalEntries > 0 && entry ? `Item ${currentPage + 1} of ${totalEntries}` : totalEntries === 0 && !loading ? 'No Items' : ''}
        </Typography>
        <IconButton onClick={() => fetchEntry(currentPage + 1)} disabled={!entry || (currentPage + 1) >= totalEntries || loading}>
          <ArrowForwardIcon />
        </IconButton>
      </Box>

      {/* Display Area for the current entry */}
      {loading && <Typography>Loading next entry...</Typography>}
      {error && !loading && <Typography color="error">{error}</Typography>}
      {!entry && !loading && !error && <Typography>No entry loaded or available for checking with current filters.</Typography>}

      {entry && (
        <>
          <Typography variant="h5" gutterBottom>
            {entry.title}
          </Typography>
          <Typography paragraph sx={{ whiteSpace: 'pre-wrap', maxHeight: '300px', overflowY: 'auto', border: '1px solid #ccc', p:1 }}>
            {entry.cleaned_text}
          </Typography>

          <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
        Sustainable Development Goals (SDGs)
      </Typography>
      {updatingSdgs && <Typography sx={{ color: 'blue', fontStyle: 'italic' }}>Updating SDGs...</Typography>}
      {sdgUpdateError && <Typography color="error">{sdgUpdateError}</Typography>}
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell sx={{ width: '10%' }}>Select</TableCell>
              <TableCell>SDG</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {Object.entries(sdgs).map(([sdgKey, sdgName]) => (
              <TableRow key={sdgKey}>
                <TableCell>
                  <Checkbox
                    checked={selectedSdgs.some(s => s.value === sdgKey)} // Update checked logic
                    onChange={(event) => handleSdgChange(sdgKey, event.target.checked)}
                    disabled={updatingSdgs}
                  />
                </TableCell>
                <TableCell>{sdgKey}: {sdgName}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Box sx={{ mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          Validation
        </Typography>
        <FormControlLabel
          control={
            <Checkbox
              checked={entry?.valid || false}
              onChange={(event) => handleValidationChange(event.target.checked)}
              disabled={!entry || updatingValidation}
            />
          }
          label="Mark as Validated"
        />
        {updatingValidation && <Typography sx={{ color: 'blue', fontStyle: 'italic', ml: 2, display: 'inline-block' }}>Updating...</Typography>}
        {validationUpdateError && <Typography color="error" sx={{ ml: 2, display: 'inline-block' }}>{validationUpdateError}</Typography>}
        
        {/* Reference Checkbox */}
        <FormControlLabel
          control={
            <Checkbox
              checked={entry?.reference || false}
              onChange={(event) => handleReferenceChange(event.target.checked)}
              disabled={!entry || updatingReference}
            />
          }
          label="Mark as Reference"
          sx={{ ml: 2 }} // Add some margin to separate from validation
        />
        {updatingReference && <Typography sx={{ color: 'blue', fontStyle: 'italic', ml: 2, display: 'inline-block' }}>Updating...</Typography>}
        {referenceUpdateError && <Typography color="error" sx={{ ml: 2, display: 'inline-block' }}>{referenceUpdateError}</Typography>}
      </Box>
        </>
      )}
    </Box>
  );
};

export default CheckPage;
