import {
  isRouteErrorResponse,
  Links,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
} from "react-router";
import React from "react";

import type { Route } from "./+types/root";
import "./app.css";

// Error boundary to catch the initial load context error
class MetaLinksErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; retryCount: number }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, retryCount: 0 };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error) {
    // Reset error state after a brief delay to retry (max 3 times)
    if (this.state.retryCount < 3) {
      setTimeout(() => {
        this.setState({ hasError: false, retryCount: this.state.retryCount + 1 });
      }, 100);
    }
  }

  render() {
    if (this.state.hasError) {
      // Return empty while waiting for retry
      return null;
    }
    return this.props.children;
  }
}

export const links: Route.LinksFunction = () => [
  { rel: "preconnect", href: "https://fonts.googleapis.com" },
  {
    rel: "preconnect",
    href: "https://fonts.gstatic.com",
    crossOrigin: "anonymous",
  },
  {
    rel: "stylesheet",
    href: "https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&display=swap",
  },
];

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="data:," />
        <link rel="apple-touch-icon" href="data:," />
        <link rel="apple-touch-icon-precomposed" href="data:," />
        <MetaLinksErrorBoundary>
          <Meta />
          <Links />
        </MetaLinksErrorBoundary>
        {/* Theme detection script - runs before React hydration */}
        <script dangerouslySetInnerHTML={{
          __html: `
            (function() {
              // Apply theme based on system preference
              const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
              if (prefersDark) {
                document.documentElement.classList.add('dark');
              }

              // Listen for theme changes
              window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
                if (e.matches) {
                  document.documentElement.classList.add('dark');
                } else {
                  document.documentElement.classList.remove('dark');
                }
              });
            })();
          `
        }} />
        {/* Auto-reload on initial container load error */}
        <script dangerouslySetInnerHTML={{
          __html: `
            (function() {
              if (typeof window !== 'undefined' && !window.__errorReloadAttempted) {
                let errorCount = 0;
                window.addEventListener('error', function(e) {
                  if (e.message && (
                    e.message.includes('Invalid hook call') ||
                    e.message.includes('Cannot read properties of null (reading \\'useContext\\')')
                  )) {
                    errorCount++;
                    if (errorCount === 1 && !window.__errorReloadAttempted) {
                      window.__errorReloadAttempted = true;
                      setTimeout(() => window.location.reload(), 1000);
                    }
                  }
                });
              }
            })();
          `
        }} />
      </head>
      <body>
        {children}
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  );
}

export default function App() {
  return <Outlet />;
}

export function ErrorBoundary({ error }: Route.ErrorBoundaryProps) {
  let message = "Oops!";
  let details = "An unexpected error occurred.";
  let stack: string | undefined;

  if (isRouteErrorResponse(error)) {
    message = error.status === 404 ? "404" : "Error";
    details =
      error.status === 404
        ? "The requested page could not be found."
        : error.statusText || details;
  } else if (import.meta.env.DEV && error && error instanceof Error) {
    details = error.message;
    stack = error.stack;
  }

  return (
    <main className="pt-16 p-4 container mx-auto">
      <h1>{message}</h1>
      <p>{details}</p>
      {stack && (
        <pre className="w-full p-4 overflow-x-auto">
          <code>{stack}</code>
        </pre>
      )}
    </main>
  );
}
