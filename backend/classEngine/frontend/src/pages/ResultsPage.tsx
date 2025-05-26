// src/ResultsPage.tsx
import React, { useEffect, useState, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Box,
  Button,
  CircularProgress, // For loading indicator
  Alert, // For error messages
  List,
  ListItem,
  ListItemText,
  Paper,
  Pagination, // Import Pagination component
  IconButton, // For up/down vote buttons
} from '@mui/material';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward'; // Up arrow icon
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward'; // Down arrow icon

// Define TypeScript interfaces for the FastAPI response models
interface Hit {
  id: string;
  title: string;
  extracted_text: string;
  sdgs: string[];
  targets: string[];
  up: number;
  down: number;
}

interface SearchResponse {
  hits: Hit[];
  total: number;
}

// Define the structure for the feedback response
interface FeedbackResponse {
  message: string;
  // You might want to include the updated up/down counts here if your API returns them
}

function ResultsPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const [sdgIds, setSdgIds] = useState<string[]>([]);
  const [keywords, setKeywords] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null);
  const [currentPage, setCurrentPage] = useState<number>(1); // State for current page
  const [itemsPerPage] = useState<number>(20); // State for items per page, can be configurable

  const FASTAPI_BASE_URL = 'https://api.innoclass.alkemata.com';

  // --- Search and Pagination Logic ---
  const fetchResults = useCallback(async (page: number) => {
    setLoading(true);
    setError(null);

    const params = new URLSearchParams(location.search);
    const sdg_ids_param = params.get('sdg_ids');
    const sdg_ids_from_url = sdg_ids_param ? sdg_ids_param.split(',').filter(id => id.trim() !== '') : [];

    const keywords_param = params.get('keywords');
    const keywords_from_url = keywords_param ? keywords_param.split('&keywords=').join(',') : '';

    setSdgIds(sdg_ids_from_url);
    setKeywords(keywords_from_url);

    try {
      const requestBody = {
        selections: sdg_ids_from_url,
        keywords: keywords_from_url,
        page: page, // Use the page parameter
        size: itemsPerPage,
      };

      console.log("Sending request to FastAPI:", requestBody);

      const response = await fetch(`${FASTAPI_BASE_URL}/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`HTTP error! status: ${response.status}, detail: ${errorData.detail || response.statusText}`);
      }

      const data: SearchResponse = await response.json();
      setSearchResults(data);
    } catch (err: any) {
      console.error('Error fetching search results:', err);
      setError(`Failed to load search results: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }, [location.search, itemsPerPage]); // Dependencies for useCallback

  useEffect(() => {
    // When the component mounts or URL search params change, reset to page 1 and fetch results
    setCurrentPage(1);
    fetchResults(1);
  }, [location.search, fetchResults]);

  const handlePageChange = (event: React.ChangeEvent<unknown>, value: number) => {
    setCurrentPage(value);
    fetchResults(value); // Fetch results for the new page
  };

  // --- Feedback Logic ---
  const handleFeedback = async (id: string, feedbackType: 'up' | 'down') => {
    try {
      const response = await fetch(`${FASTAPI_BASE_URL}/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ id, feedback_type: feedbackType }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`HTTP error! status: ${response.status}, detail: ${errorData.detail || response.statusText}`);
      }

      const data: FeedbackResponse = await response.json();
      console.log('Feedback response:', data.message);

      // Optionally, update the UI to reflect the new up/down counts
      // This assumes your FastAPI /feedback endpoint returns the updated counts for the specific hit
      // If it doesn't, you might need to re-fetch the search results for the current page
      setSearchResults(prevResults => {
        if (!prevResults) return null;

        const updatedHits = prevResults.hits.map(hit => {
          if (hit.id === id) {
            return {
              ...hit,
              up: feedbackType === 'up' ? hit.up + 1 : hit.up,
              down: feedbackType === 'down' ? hit.down + 1 : hit.down,
            };
          }
          return hit;
        });
        return { ...prevResults, hits: updatedHits };
      });

    } catch (err: any) {
      console.error('Error sending feedback:', err);
      alert(`Failed to send feedback: ${err.message}`); // Simple alert for user feedback
    }
  };

  const totalPages = searchResults ? Math.ceil(searchResults.total / itemsPerPage) : 0;

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            InnoClass
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
        <Typography variant="h4" component="h2" gutterBottom>
          Search Results
        </Typography>

        <Typography variant="h6" gutterBottom>
          Search Criteria:
        </Typography>
        <Typography paragraph>
          **Selected SDG IDs:** {sdgIds.length > 0 ? sdgIds.join(', ') : 'No SDGs selected.'}
        </Typography>
        <Typography paragraph>
          **Keywords:** {keywords || 'No keywords entered.'}
        </Typography>

        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
            <CircularProgress />
            <Typography sx={{ ml: 2 }}>Loading results...</Typography>
          </Box>
        )}

        {error && (
          <Alert severity="error" sx={{ my: 4 }}>
            {error}
          </Alert>
        )}

        {searchResults && !loading && !error && (
          <Box sx={{ mt: 4 }}>
            <Typography variant="h5" gutterBottom>
              Total Hits: {searchResults.total}
            </Typography>
            {searchResults.hits.length > 0 ? (
              // Start of the React Fragment
              <React.Fragment>
                <List>
                  {searchResults.hits.map((hit) => (
                    <Paper key={hit.id} elevation={1} sx={{ mb: 2, p: 2 }}>
                      <ListItem alignItems="flex-start" secondaryAction={
                        <Box>
                          <IconButton aria-label="upvote" onClick={() => handleFeedback(hit.id, 'up')}>
                            <ArrowUpwardIcon />
                          </IconButton>
                          <IconButton aria-label="downvote" onClick={() => handleFeedback(hit.id, 'down')}>
                            <ArrowDownwardIcon />
                          </IconButton>
                        </Box>
                      }>
                        <ListItemText
                          primary={
                            <Typography variant="h6" component="span">
                              {hit.title}
                            </Typography>
                          }
                          secondary={
                            <>
                              <Typography
                                sx={{ display: 'block' }}
                                component="span"
                                variant="body2"
                                color="text.primary"
                              >
                                Extracted Text: {hit.cleaned_text || 'N/A'}
                              </Typography>
                              <Typography component="span" variant="body2" color="text.secondary">
                                SDGs: {hit.sdg.join(', ') || 'N/A'} | Targets: {hit.targets.join(', ') || 'N/A'}
                              </Typography>
                              <Typography component="span" variant="body2" color="text.secondary">
                                <br />Up Votes: {hit.up} | Down Votes: {hit.down}
                              </Typography>
                            </>
                          }
                        />
                      </ListItem>
                    </Paper>
                  ))}
                </List>

                {/* Pagination Component */}
                {totalPages > 1 && (
                  <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
                    <Pagination
                      count={totalPages}
                      page={currentPage}
                      onChange={handlePageChange}
                      color="primary"
                      showFirstButton
                      showLastButton
                    />
                  </Box>
                )}
              </React.Fragment> // End of the React Fragment
            ) : (
              <Typography>No results found for your search criteria.</Typography>
            )}
          </Box>
        )}

        <Button
          variant="contained"
          onClick={() => navigate('/search')}
          sx={{ mt: 4 }}
        >
          Go Back to Search
        </Button>
      </Container>
    </Box>
  );
}

export default ResultsPage;