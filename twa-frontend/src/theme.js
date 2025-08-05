import { createTheme } from '@mui/material/styles';

// Ilovamiz uchun qorong'u (dark) tema
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#58a6ff', // Ko'k rang
    },
    background: {
      default: '#0d1117', // Orqa fon
      paper: '#161b22',   // Kartochkalar foni
    },
    text: {
      primary: '#c9d1d9',
      secondary: '#8b949e',
    },
  },
  components: {
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            '& fieldset': {
              borderColor: '#30363d',
            },
            '&:hover fieldset': {
              borderColor: '#58a6ff',
            },
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: '6px',
        },
      },
    },
  },
});

export default theme;
