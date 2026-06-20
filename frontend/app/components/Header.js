/**
 * Header.js — the top bar + sub-nav, reused on every page.
 * Matches the BookMyShow screenshot: logo, search, city, Sign in, and the
 * Movies/Stream/Events/... nav row.
 *
 * It's a plain presentational component (no state), so it can be a server
 * component — but we keep it simple and let Next decide.
 */
import Link from "next/link";
import Logo from "./Logo";
import CitySelector from "./CitySelector";
import SearchBar from "./SearchBar";
import SignIn from "./SignIn";

export default function Header() {
  return (
    <header className="header">
      <div className="container header-top">
        <Link href="/" aria-label="BookMyShow" style={{ display: "flex", alignItems: "center" }}>
          <Logo width={115} dark />
        </Link>
        <SearchBar />
        <div className="header-right">
          <CitySelector />
          <SignIn />
        </div>
      </div>
      <div className="subnav">
        <div className="container subnav-inner">
          <div className="subnav-group">
            <Link href="/">Movies</Link>
            <a>Stream</a><a>Events</a><a>Plays</a><a>Sports</a><a>Activities</a>
          </div>
          <div className="subnav-group right">
            <a>ListYourShow</a><a>Corporates</a><a>Offers</a><a>Gift Cards</a>
          </div>
        </div>
      </div>
    </header>
  );
}
