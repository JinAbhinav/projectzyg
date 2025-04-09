import React from 'react';
import { ThemeProvider } from 'next-themes';
import { Toaster } from 'sonner';
import '../styles/globals.css';

export default function App({ Component, pageProps }) {
  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      <Component {...pageProps} />
      <Toaster position="top-right" richColors />
    </ThemeProvider>
  );
} 