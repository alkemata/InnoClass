// src/ResultsPage.tsx
import React, { useEffect, useState } from 'react';
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
} from '@mui/material';

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

function ResultsPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const [sdgIds, setSdgIds] = useState<string[]>([]);
  const [keywords, setKeywords] = useState<string>(''); // Keywords are a single string in your FastAPI model
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null);

  // You might want to make this configurable, e.g., in an environment variable
  const FASTAPI_BASE_URL = 'https://api.innoclass.alkemata.com'; // Replace with your actual FastAPI base URL

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const sdg_ids_param = params.get('sdg_ids');
    const sdg_ids_from_url = sdg_ids_param ? sdg_ids_param.split(',').filter(id => id.trim() !== '') : [];

    // Keywords are passed as a single string from the search page's text area
    // The FastAPI expects a single string for keywords, so we'll re-join them if they came as multiples
    const keywords_param = params.get('keywords');
    const keywords_from_url = keywords_param ? keywords_param.split('&keywords=').join(',') : ''; // Re-join them into a single string if needed

    setSdgIds(sdg_ids_from_url);
    setKeywords(keywords_from_url);

    const fetchResults = async () => {
      setLoading(true);
      setError(null); // Clear previous errors

      try {
        const requestBody = {
          category: 'sdgs', // Based on your FastAPI route, this is fixed for now
          selections: sdg_ids_from_url,
          keywords: keywords_from_url,
          page: 1, // Defaulting for now, you could add pagination later
          size: 20, // Defaulting for now
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
    };

    fetchResults();
  }, [location.search]); // Re-run effect when URL search params change

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
              <List>
                {searchResults.hits.map((hit) => (
                  <Paper key={hit.id} elevation={1} sx={{ mb: 2, p: 2 }}>
                    <ListItem alignItems="flex-start">
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
                              Extracted Text: {hit.extracted_text || 'N/A'}
                            </Typography>
                            <Typography component="span" variant="body2" color="text.secondary">
                              SDGs: {hit.sdgs.join(', ') || 'N/A'} | Targets: {hit.targets.join(', ') || 'N/A'}
                            </Typography>
                            <Typography component="span" variant="body2" color="text.secondary">
                              <br/>Up Votes: {hit.up} | Down Votes: {hit.down}
                            </Typography>
                          </>
                        }
                      />
                    </ListItem>
                  </Paper>
                ))}
              </List>
            ) : (
              <Typography>No results found for your search criteria.</Typography>
            )}
          </Box>
        )}

        <Button
          variant="contained"
          onClick={() => navigate('/')}
          sx={{ mt: 4 }}
        >
          Go Back to Search
        </Button>
      </Container>
    </Box>
  );
}

export default ResultsPage;