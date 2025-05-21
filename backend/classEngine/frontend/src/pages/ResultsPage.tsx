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
} from '@mui/material';

function ResultsPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const [sdgIds, setSdgIds] = useState<string[]>([]);
  const [keywords, setKeywords] = useState<string[]>([]);
  const [fastApiUrl, setFastApiUrl] = useState<string>('');

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const sdg_ids_param = params.get('sdg_ids');
    const sdg_ids = sdg_ids_param ? sdg_ids_param.split(',') : [];

    // The 'keywords' parameter might appear multiple times
    const keywords_params = params.getAll('keywords');
    const kws: string[] = keywords_params.flatMap(kw => kw.split(',').map(item => item.trim()));


    setSdgIds(sdg_ids);
    setKeywords(kws);

    // Construct the FastAPI URL (replace with your actual FastAPI endpoint)
    const baseUrl = 'http://api.innoclass.alkemata.com/search'; // Example FastAPI endpoint
    const queryParams = new URLSearchParams();
    sdg_ids.forEach(id => queryParams.append('sdg_ids', id));
    kws.forEach(kw => queryParams.append('keywords', kw));

    setFastApiUrl(`${baseUrl}?${queryParams.toString()}`);

    // In a real application, you would make an API call here:
    // fetch(fastApiUrl)
    //   .then(response => response.json())
    //   .then(data => {
    //     // Process and display your results
    //     console.log('FastAPI Response:', data);
    //   })
    //   .catch(error => console.error('Error fetching data:', error));

  }, [location.search]);

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
          Selected SDG IDs:
        </Typography>
        <Typography paragraph>
          {sdgIds.length > 0 ? sdgIds.join(', ') : 'No SDGs selected.'}
        </Typography>

        <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
          Keywords:
        </Typography>
        <Typography paragraph>
          {keywords.length > 0 ? keywords.join(', ') : 'No keywords entered.'}
        </Typography>

        <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
          Simulated FastAPI Query:
        </Typography>
        <Typography paragraph sx={{ fontStyle: 'italic', wordBreak: 'break-all' }}>
          {fastApiUrl}
        </Typography>

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