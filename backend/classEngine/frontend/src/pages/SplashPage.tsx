import React, { useEffect } from 'react';
import { Box, Typography, createTheme, ThemeProvider } from '@mui/material';
import { useNavigate } from 'react-router-dom'; // Import useNavigate for redirection

// Define a custom Material UI theme.
const theme = createTheme({
  typography: {
    fontFamily: 'Inter, sans-serif',
  },
  palette: {
    primary: {
      main: '#F97316', // Vibrant Orange
    },
    secondary: {
      main: '#22C55E', // Bright Green
    },
  },
});

// Define the SplashScreen component.
const SplashScreen = () => {
  const navigate = useNavigate(); // Hook to programmatically navigate

  // useEffect hook to manage the splash screen's duration and redirection.
  useEffect(() => {
    // Set a timer to redirect after 5000 milliseconds (5 seconds).
    const timer = setTimeout(() => {
      navigate('/menu'); // Redirect to the /search route
    }, 5000); // 5 seconds

    // Create a style element and append it to the head
    const styleElement = document.createElement('style');
    styleElement.textContent = `
      /* Import Google Font 'Inter' for consistent typography. */
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');

      /* Ensure html, body, and the root div take full height and prevent scrolling. */
      html, body, #root {
        height: 100%;
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
    `;
    document.head.appendChild(styleElement);

    // Cleanup function: Clear the timer and remove the style element when the component unmounts.
    return () => {
      clearTimeout(timer);
      document.head.removeChild(styleElement);
    };
  }, [navigate]); // Add navigate to dependency array

  return (
    <ThemeProvider theme={theme}>
      {/* Main container for the Splash Screen. */}
      <Box
        sx={{
          position: 'relative',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          overflow: 'hidden',
          backgroundColor: 'white',
        }}
      >
        {/* Background light particles for an ethereal effect. */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            zIndex: 0,
            overflow: 'hidden',
          }}
        >
          {/* Generate 40 random light particles. */}
          {Array.from({ length: 40 }).map((_, i) => (
            <div
              key={i} // Unique key for each particle.
              className="animate-light-particle" // Apply animation class
              style={{
                position: 'absolute',
                backgroundColor: '#D1D5DB', // Light gray color for contrast on white background
                borderRadius: '9999px', // Full rounded corners
                opacity: 0,
                width: `${Math.random() * 4 + 2}px`,
                height: `${Math.random() * 4 + 2}px`,
                top: `${Math.random() * 100}%`,
                left: `${Math.random() * 100}%`,
                animationDelay: `${Math.random() * 5}s`,
                animationDuration: `${Math.random() * 6 + 4}s`,
                '--translate-x': `${(Math.random() - 0.5) * 200}px`,
                '--translate-y': `${(Math.random() - 0.5) * 200}px`,
              }}
            ></div>
          ))}
        </div>

        {/* The "InnoClass AI" text display. */}
        <Typography
          variant="h2" // Material UI Typography component for large text.
          sx={{
            position: 'relative',
            zIndex: 10,
            fontWeight: 800, // Equivalent to font-extrabold
            color: '#1F2937', // Equivalent to text-gray-900
            textAlign: 'center',
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
              className="animate-fade-in"
              style={{ display: 'inline-block', animationDelay: `${index * 0.1}s` }} // Stagger animation for each character.
            >
              {/* Use non-breaking space for actual space characters to maintain layout. */}
              {char === ' ' ? '\u00A0' : char}
            </span>
          ))}
        </Typography>
      </Box>
    </ThemeProvider>
  );
};

export default SplashScreen;
