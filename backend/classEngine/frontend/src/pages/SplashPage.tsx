import React, { useState, useEffect } from 'react';
import { Box, Typography, createTheme, ThemeProvider } from '@mui/material';

// Define a custom Material UI theme.
// This allows you to centralize typography settings and color palettes.
const theme = createTheme({
  typography: {
    // Set the default font family to 'Inter' for a modern look.
    fontFamily: 'Inter, sans-serif',
  },
  palette: {
    // Define primary and secondary colors for potential future use in your app.
    primary: {
      main: '#F97316', // Vibrant Orange
    },
    secondary: {
      main: '#22C55E', // Bright Green
    },
  },
});

function App() {
  // State to control the visibility of the splash screen.
  // It's initially true, meaning the splash screen is shown.
  const [showSplash, setShowSplash] = useState(true);

  // useEffect hook to manage the splash screen's duration.
  // This runs once after the initial render (due to empty dependency array []).
  useEffect(() => {
    // Set a timer to hide the splash screen after 4000 milliseconds (4 seconds).
    const timer = setTimeout(() => {
      setShowSplash(false); // Set state to false to hide the splash screen.
    }, 4000);

    // Cleanup function: This runs when the component unmounts or before the effect re-runs.
    // It clears the timer to prevent memory leaks if the component is unmounted prematurely.
    return () => clearTimeout(timer);
  }, []); // Empty dependency array ensures this effect runs only once.

  // Conditional rendering: If showSplash is false, render the main app content.
  if (!showSplash) {
    return (
      <ThemeProvider theme={theme}>
        <Box className="flex items-center justify-center min-h-screen bg-gray-900 text-white">
          <Typography variant="h4">
            Welcome to InnoClass AI demonstrator
          </Typography>
        </Box>
      </ThemeProvider>
    );
  }

  // Render the splash screen content when showSplash is true.
  return (
    <ThemeProvider theme={theme}>
      {/* Main container for the splash screen.
          Uses Tailwind CSS classes for full screen, centering, and a white background. */}
      <Box className="relative flex items-center justify-center min-h-screen overflow-hidden bg-white">
        {/* Background light particles for an ethereal effect. */}
        <div className="absolute inset-0 z-0 overflow-hidden">
          {/* Generate 40 random light particles. */}
          {Array.from({ length: 40 }).map((_, i) => (
            <div
              key={i} // Unique key for each particle.
              className="absolute bg-gray-300 rounded-full opacity-0 animate-light-particle" // Changed particle color for contrast
              style={{
                // Random size for variety.
                width: `${Math.random() * 4 + 2}px`,
                height: `${Math.random() * 4 + 2}px`,
                // Random starting position within the screen.
                top: `${Math.random() * 100}%`,
                left: `${Math.random() * 100}%`,
                // Staggered animation delays for a more natural look.
                animationDelay: `${Math.random() * 5}s`,
                // Random animation duration for varied movement.
                animationDuration: `${Math.random() * 6 + 4}s`,
                // Custom CSS variables for random translation in the animation.
                '--translate-x': `${(Math.random() - 0.5) * 200}px`,
                '--translate-y': `${(Math.random() - 0.5) * 200}px`,
              }}
            ></div>
          ))}
        </div>

        {/* The "InnoClass AI" text display. */}
        <Typography
          variant="h2" // Material UI Typography component for large text.
          className="relative z-10 font-extrabold text-gray-900 text-center" // Changed text color to dark gray
          sx={{
            // Responsive font size using Material UI's `sx` prop for different breakpoints.
            fontSize: { xs: '3rem', sm: '4rem', md: '6rem', lg: '8rem' },
            // Text shadow for a vibrant glow effect, combining white, orange, and green.
            textShadow: '0 0 10px #F97316, 0 0 20px #F97316, 0 0 30px #22C55E, 0 0 40px #22C55E, 0 0 50px #F97316, 0 0 60px #F97316, 0 0 70px #F97316', // Adjusted shadow to be more visible on white
            // Apply the 'glow' animation.
            animation: 'glow 1.5s ease-in-out infinite alternate',
          }}
        >
          {/* Split the text into individual characters to apply staggered animations. */}
          {'InnoClass AI'.split('').map((char, index) => (
            <span
              key={index} // Unique key for each character span.
              className="inline-block animate-fade-in"
              style={{ animationDelay: `${index * 0.1}s` }} // Stagger animation for each character.
            >
              {/* Use non-breaking space for actual space characters to maintain layout. */}
              {char === ' ' ? '\u00A0' : char}
            </span>
          ))}
        </Typography>

        {/* Global CSS for animations and basic styling. */}
        {/* The 'jsx' prop on the style tag is a common convention in some React setups
            to indicate that the CSS is scoped or related to this component. */}
        <style jsx>{`
          /* Import Google Font 'Inter' for consistent typography. */
          @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');

          /* Ensure html, body, and the root div take full height and prevent scrolling. */
          html, body, #root {
            height: 100%;
            widht: 80%;
            margin: 0;
            overflow: hidden; /* Prevents scrollbars during the splash screen display. */
          }

          /* Keyframe animation for text fade-in effect. */
          @keyframes fade-in {
            from {
              opacity: 0;
              transform: translateY(20px) scale(0.8); /* Start slightly below and smaller. */
            }
            to {
              opacity: 1;
              transform: translateY(0) scale(1); /* End at original position and size. */
            }
          }

          /* Apply the fade-in animation to elements with this class. */
          .animate-fade-in {
            animation: fade-in 0.8s ease-out forwards; /* 'forwards' keeps the final state. */
          }

          /* Keyframe animation for the pulsating glow effect on the text. */
          @keyframes glow {
            from {
              /* Initial text shadow with slightly less spread. */
              text-shadow: 0 0 10px #F97316, 0 0 20px #F97316, 0 0 30px #22C55E, 0 0 40px #22C55E, 0 0 50px #F97316, 0 0 60px #F97316, 0 0 70px #F97316;
            }
            to {
              /* Increased text shadow spread for the 'glow' effect. */
              text-shadow: 0 0 20px #F97316, 0 0 30px #F97316, 0 0 40px #22C55E, 0 0 50px #22C55E, 0 0 60px #F97316, 0 0 70px #F97316, 0 0 80px #F97316;
            }
          }

          /* Keyframe animation for the background light particles. */
          @keyframes light-particle {
            0% {
              opacity: 0;
              transform: translate(0, 0) scale(0.5); /* Start invisible, small, at original position. */
            }
            25% {
              opacity: 0.8; /* Become visible. */
            }
            100% {
              opacity: 0;
              /* Move to a random translated position and grow, then fade out.
                 Uses CSS variables set in inline style for random movement. */
              transform: translate(var(--translate-x), var(--translate-y)) scale(1.5);
            }
          }

          /* Apply the light particle animation. */
          .animate-light-particle {
            animation: light-particle var(--animation-duration) ease-out infinite;
          }
        `}</style>
      </Box>
    </ThemeProvider>
  );
}

export default App;
