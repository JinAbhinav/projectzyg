import React from 'react';
import Head from 'next/head';
import { Navbar } from './navbar';

export function Layout({ children, title = 'SEER - Cyber Threat Intelligence' }) {
  return (
    <>
      <Head>
        <title>{title}</title>
        <meta name="description" content="SEER - AI-Powered Cyber Threat Prediction & Early Warning System" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="flex min-h-screen bg-background">
        <Navbar />

        <div className="flex-1">
          <main className="p-6 md:p-8 max-w-7xl mx-auto">
            {children}
          </main>
        </div>
      </div>
    </>
  );
} 