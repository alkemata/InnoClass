import React from 'react';
import { Box, List, ListItem, ListItemButton, ListItemText, Typography, Paper, CssBaseline } from '@mui/material';
import { createTheme, ThemeProvider } from '@mui/material/styles';
import { useNavigate } from 'react-router-dom';

// Define a custom Material-UI theme for consistent styling, including Inter font.
const theme = createTheme({
  typography: {
    fontFamily: 'Inter, sans-serif',
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: `
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
      `,
    },
  },
});

/**
 * Main application component for the Menu Page.
 * Displays a list of navigation links centered on the screen.
 */
function Menu() {
  /**
   * Handles navigation for menu items.
   * For internal pages, it logs a message (in a real app, this would use a router).
   * For external URLs, it opens the link in a new tab.
   * @param {string} page - Identifier for the page to navigate to ('search', 'classification', 'operations').
   */
  const navigate = useNavigate(); 
  const handleNavigation = (page: string) => {
    if (page === 'search') {
      // In a real application, you would use a routing library (e.g., React Router DOM) here:
      navigate('/search');
      //console.log('Navigating to internal Search page...');
    } else if (page === 'classification') {
      // In a real application:
      navigate('/check-classification');
      //console.log('Navigating to internal Check Classification page...');
    } else if (page === 'operations') {
      // Opens the external URL in a new browser tab.
      window.open('https://dagster.innoclass.alkemata.com', '_blank');
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline /> {/* Provides a consistent baseline for styling across browsers */}
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column', // Arrange items vertically
          justifyContent: 'center', // Center content vertically
          alignItems: 'center',     // Center content horizontally
          minHeight: '100vh',       // Take full viewport height
          backgroundColor: '#f0f2f5', // Light background color for the page
          p: 2, // Add some padding around the content
        }}
      >
        <Paper
          elevation={6} // Adds a shadow for depth
          sx={{
            p: { xs: 3, sm: 4 }, // Responsive padding: 3 on small screens, 4 on larger
            borderRadius: 3,     // Rounded corners for the paper box
            backgroundColor: '#ffffff', // White background for the box
            textAlign: 'center', // Center text within the box
            minWidth: { xs: '90%', sm: 300, md: 400 }, // Responsive width
            maxWidth: 450,       // Maximum width to prevent it from getting too wide
            boxShadow: '0 8px 16px rgba(0, 0, 0, 0.1)', // Custom shadow for a softer look
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}
        >
          <Typography
            variant="h4"
            component="h1"
            gutterBottom
            sx={{
              mb: { xs: 2, sm: 3 }, // Responsive margin-bottom
              color: '#333',       // Darker text color for the title
              fontWeight: 600,     // Make the title bold
            }}
          >
            Main Menu
          </Typography>
          <List sx={{ width: '100%' }}> {/* List takes full width of its parent Paper */}
            {/* Search Link */}
            <ListItem disablePadding>
              <ListItemButton
                onClick={() => handleNavigation('search')}
                sx={{
                  borderRadius: 2, // Rounded corners for the button
                  mb: 1.5,         // Margin-bottom between list items
                  py: 1.5,         // Vertical padding
                  px: 3,           // Horizontal padding
                  // Hover effects for visual feedback
                  '&:hover': {
                    backgroundColor: '#e0f7fa', // Light blue on hover
                    transform: 'scale(1.02)',   // Slightly enlarge on hover
                    transition: 'transform 0.2s ease-in-out', // Smooth transition
                  },
                }}
              >
                <ListItemText
                  primary="Search"
                  primaryTypographyProps={{
                    variant: 'h6',         // Larger text for the link
                    fontWeight: 'medium',  // Medium font weight
                    color: '#007bff',      // Blue color for the link
                  }}
                />
              </ListItemButton>
            </ListItem>

            {/* Check Classification Link */}
            <ListItem disablePadding>
              <ListItemButton
                onClick={() => handleNavigation('classification')}
                sx={{
                  borderRadius: 2,
                  mb: 1.5,
                  py: 1.5,
                  px: 3,
                  '&:hover': {
                    backgroundColor: '#e3f2fd', // Light blue on hover
                    transform: 'scale(1.02)',
                    transition: 'transform 0.2s ease-in-out',
                  },
                }}
              >
                <ListItemText
                  primary="Check classification"
                  primaryTypographyProps={{
                    variant: 'h6',
                    fontWeight: 'medium',
                    color: '#28a745', // Green color for the link
                  }}
                />
              </ListItemButton>
            </ListItem>

            {/* Operations Link (External URL) */}
            <ListItem disablePadding>
              <ListItemButton
                component="a" // Renders the ListItemButton as an HTML anchor tag
                href="https://example.com/operations" // The external URL
                target="_blank" // Opens the link in a new tab
                rel="noopener noreferrer" // Security best practice for target="_blank"
                sx={{
                  borderRadius: 2,
                  py: 1.5,
                  px: 3,
                  '&:hover': {
                    backgroundColor: '#ffe0b2', // Light orange on hover
                    transform: 'scale(1.02)',
                    transition: 'transform 0.2s ease-in-out',
                  },
                }}
              >
                <ListItemText
                  primary="Operations"
                  primaryTypographyProps={{
                    variant: 'h6',
                    fontWeight: 'medium',
                    color: '#ffc107', // Orange color for the link
                  }}
                />
              </ListItemButton>
            </ListItem>
            </List>
            </Paper></Box></ThemeProvider>)}
