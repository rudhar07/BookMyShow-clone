/**
 * Logo.js — the official BookMyShow logo, served from our own app.
 * ================================================================
 * The real site renders the logo as an SVG (115×50 in the header). We saved
 * BookMyShow's actual logo file to `public/bms-logo.svg` and render it here, so:
 *   • it's the EXACT artwork (red ticket + "bookmyshow" wordmark), and
 *   • it's self-contained — served by our own frontend, no external CDN or CORS
 *     dependency, works offline.
 *
 * Files placed in Next.js's `public/` folder are served at the site root, so
 * `public/bms-logo.svg` is reachable at `/bms-logo.svg`. We use a plain <img>
 * with width fixed and height auto to keep the logo's natural aspect ratio
 * (the file is 115×33.9), avoiding any distortion.
 *
 * IMPORTANT — two variants:
 *   The real logo's "book"/"show" wordmark is WHITE; only the "my" ticket is red.
 *   • On the dark FOOTER the white text shows fine → use `bms-logo.svg`.
 *   • On the white HEADER white text is invisible (you'd see only the red "my"),
 *     so we use `bms-logo-dark.svg` (same artwork, wordmark recoloured dark).
 *   Pass `dark` to get the dark-text header version. This is exactly the
 *   light-logo / dark-logo split BookMyShow itself ships (`icon-bms-logo-dark`).
 */
export default function Logo({ width = 115, dark = false, className = "" }) {
  return (
    <img
      src={dark ? "/bms-logo-dark.svg" : "/bms-logo.svg"}
      alt="BookMyShow"
      width={width}
      style={{ height: "auto", display: "block" }}
      className={className}
    />
  );
}
