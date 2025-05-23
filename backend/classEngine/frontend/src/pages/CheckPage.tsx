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
  FormControlLabel, // Import FormControlLabel
} from '@mui/material';
import { AxiosError } from 'axios'; // Import AxiosError
import api from '../api';
import sdgsData from '../data/sdgs.json';

interface EntryData {
  id: string;
  title: string;
  cleaned_text: string;
  sdg: string[];
  target: string[];
  valid: boolean;
}

interface SdgDefinition {
  [key: string]: string;
}

const sdgs: SdgDefinition = sdgsData;

const CheckPage: React.FC = () => {
  const [entry, setEntry] = useState<EntryData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSdgs, setSelectedSdgs] = useState<string[]>([]);
  const [updatingSdgs, setUpdatingSdgs] = useState<boolean>(false);
  const [sdgUpdateError, setSdgUpdateError] = useState<string | null>(null);
  const [updatingValidation, setUpdatingValidation] = useState<boolean>(false);
  const [validationUpdateError, setValidationUpdateError] = useState<string | null>(null);

  useEffect(() => {
    const fetchEntry = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await api.get<EntryData>('/check/next_entry');
        setEntry(response.data);
        setSelectedSdgs(response.data.sdg || []); // Initialize with existing SDGs or empty array
        setLoading(false);
      } catch (err) {
        const axiosError = err as AxiosError;
        if (axiosError.isAxiosError && axiosError.response?.status === 404) {
          setError('No more unvalidated entries found.');
        } else {
          setError('Failed to fetch data. Please try again later.');
          console.error("Fetch error:", err); // Log error for debugging
        }
        setLoading(false);
        setEntry(null); // Ensure no stale data is shown
      }
    };

    fetchEntry();
  }, []);

  const handleSdgChange = async (sdgKey: string, isChecked: boolean) => {
    if (!entry || !entry.id) {
      console.error("No entry loaded or entry ID is missing. Cannot update SDGs.");
      setSdgUpdateError("Cannot update SDGs: No active entry.");
      return;
    }

    const newSelectedSdgs = isChecked
      ? [...selectedSdgs, sdgKey]
      : selectedSdgs.filter(s => s !== sdgKey);

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

  if (loading) {
    return <Typography>Loading...</Typography>;
  }

  if (error) {
    return <Typography color="error">{error}</Typography>;
  }

  if (!entry) {
    return <Typography>No entry loaded or available for checking.</Typography>;
  }

  return (
    <Box sx={{ p: 2 }}>
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
                    checked={selectedSdgs.includes(sdgKey)}
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
        {updatingValidation && <Typography sx={{ color: 'blue', fontStyle: 'italic', ml: 2 }}>Updating validation status...</Typography>}
        {validationUpdateError && <Typography color="error" sx={{ ml: 2 }}>{validationUpdateError}</Typography>}
      </Box>
    </Box>
  );
};

export default CheckPage;
