/**
 * layout.js — the ROOT layout wrapping every page (Next.js App Router).
 *
 * Whatever is in `children` (the current page) renders inside this shell, so the
 * Header + Footer appear on all pages without repeating them. This is Next's
 * "nested layouts" feature and a key talking point: shared chrome lives once.
 */
import "./globals.css";
import Header from "./components/Header";
import Footer from "./components/Footer";
import { CityProvider } from "./components/CityContext";
import { AuthProvider } from "./components/AuthContext";

export const metadata = {
  title: "BookMyShow Clone",
  description: "Movie ticket booking — full-stack project",
  // Browser-tab icon = BookMyShow's red ticket mark (icon-bms-logo-small).
  icons: { icon: "/bms-logo-icon.svg" },
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <CityProvider>
            <Header />
            <main>{children}</main>
            <Footer />
          </CityProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
