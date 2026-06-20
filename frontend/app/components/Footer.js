/**
 * Footer.js — the big BookMyShow SEO footer (from the TOON).
 * ==========================================================
 * TEACHING POINT: the footer is dozens of links. Hand-writing each <a> would be
 * 150 lines of copy-paste. Instead we treat the links as DATA (arrays) and render
 * them with .map(). This is "data-driven rendering" — the single most important
 * React habit: describe the data, let one piece of JSX render all of it. Add a
 * link tomorrow? Edit the array, not the markup.
 *
 * The structure mirrors the TOON exactly:
 *   foot-cta (List your Show)  → foot-support (3 help links)
 *   → foot-seo (link groups)   → foot-bottom (logo + social + copyright)
 */
import Logo from "./Logo";

// Each group = one heading + its list of link labels. Pure data.
const SEO_GROUPS = [
  {
    title: "Movies Now Showing in Bengaluru",
    links: ["Cocktail 2", "Maa Inti Bangaaram", "Toy Story 5", "Obsession",
            "Kalasipalya", "Nooru Sami", "Balan: The Boy",
            "Spider-Man: Brand New Day", "Peddi", "Main Vaapas Aaunga"],
  },
  {
    title: "Movies By Genre",
    links: ["Drama Movies", "Thriller Movies", "Action Movies", "Comedy Movies",
            "Romantic Movies", "Family Movies", "Adventure Movies",
            "Sci-Fi Movies", "Fantasy Movies", "Horror Movies"],
  },
  {
    title: "Movies By Language",
    links: ["Movies in English", "Movies in Hindi", "Movies in Telugu",
            "Movies in Tamil", "Movies in Kannada", "Movies in Malayalam",
            "Movies in Bengali"],
  },
  {
    title: "Movies By Format",
    links: ["Movies in 2D", "Movies in 3D", "Movies in 4DX", "Movies in IMAX 2D",
            "Movies in IMAX 3D", "Movies in 4DX 3D", "Movies in ICE",
            "Movies in DOLBY CINEMA 2D", "Movies in SCREEN X", "Movies in MX4D"],
  },
  {
    title: "Events in Top Cities",
    links: ["Events in Mumbai", "Events in Delhi-NCR", "Events in Chennai",
            "Events in Bengaluru", "Events in Hyderabad", "Events in Pune",
            "Events in Ahmedabad", "Events in Kolkata", "Events in Kochi"],
  },
  {
    title: "Cinemas in Top Cities",
    links: ["Cinemas in Mumbai", "Cinemas in Delhi-NCR", "Cinemas in Chennai",
            "Cinemas in Bengaluru", "Cinemas in Hyderabad", "Cinemas in Pune",
            "Cinemas in Ahmedabad", "Cinemas in Kolkata", "Cinemas in Kochi"],
  },
  {
    title: "Help",
    links: ["About Us", "Contact Us", "Current Opening", "Press Release",
            "Press Coverage", "FAQs", "Terms and Conditions", "Privacy Policy"],
  },
  {
    title: "BookMyShow Exclusives",
    links: ["Lollapalooza India", "BookAChange", "Corporate Vouchers",
            "Gift Cards", "List My Show", "Offers", "Stream", "Trailers"],
  },
];

const SUPPORT = [
  "24/7 CUSTOMER CARE",
  "RESEND BOOKING CONFIRMATION",
  "SUBSCRIBE TO THE NEWSLETTER",
];

const SOCIAL = ["📘", "✖️", "📷", "▶️", "📌", "in"];

export default function Footer() {
  return (
    <footer className="footer">
      {/* List your Show CTA */}
      <div className="foot-cta">
        <div className="container foot-cta-inner">
          <div className="foot-cta-left">
            <span className="foot-hut">🏠</span>
            <div>
              <b>List your Show</b>
              <span className="sub">
                Got a show, event, activity or a great experience? Partner with
                us &amp; get listed on BookMyShow
              </span>
            </div>
          </div>
          <button>Contact today!</button>
        </div>
      </div>

      {/* Support row */}
      <div className="foot-support">
        <div className="container foot-support-inner">
          {SUPPORT.map((s) => (
            <a key={s}>{s}</a>
          ))}
        </div>
      </div>

      {/* SEO link groups — rendered from data */}
      <div className="foot-seo">
        <div className="container foot-seo-inner">
          {SEO_GROUPS.map((g) => (
            <div className="foot-group" key={g.title}>
              <h4>{g.title}</h4>
              <div className="foot-links">
                {g.links.map((l) => (
                  <a key={l}>{l}</a>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Logo + social + copyright */}
      <div className="foot-bottom">
        <div className="foot-logo">
          <Logo width={115} />
        </div>
        <div className="foot-social">
          {SOCIAL.map((s, i) => (
            <a key={i}>{s}</a>
          ))}
        </div>
        <div className="foot-copy">
          Copyright 2026 © BookMyShow Clone. This is a learning project — all
          trademarks belong to their respective owners. Built with Next.js,
          FastAPI &amp; SQLite.
        </div>
      </div>
    </footer>
  );
}
