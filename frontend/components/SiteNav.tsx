"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";

const NAV_LINKS = [
  { href: "/", label: "New Campaign" },
  { href: "/calendar", label: "Calendar" },
  { href: "/profiles", label: "Profiles" },
  { href: "/photos", label: "Photos" },
];

/**
 * Top nav with a sliding active-link pill — the same Framer Motion
 * layoutId shared-layout technique used for the Profiles page's card
 * expand, applied to a simpler case: one highlight element that glides
 * from the previous active link to the new one on navigation, instead of
 * an instant on/off state change.
 *
 * Colors are navy-on-white (not white-on-navy) — the header itself is a
 * white bar, not the navy banner it used to be, since the logo file is a
 * flattened raster image with no safe way to recolor it for a dark
 * background. See RootLayout's header comment.
 */
export function SiteNav() {
  const pathname = usePathname();

  return (
    <nav className="flex gap-1 text-sm font-semibold">
      {NAV_LINKS.map(({ href, label }) => {
        const active = pathname === href;
        return (
          <Link key={href} href={href} className="relative px-3 py-2">
            {active && (
              <motion.span
                layoutId="nav-active-pill"
                className="absolute inset-0 rounded-md bg-sky-blue/15"
                transition={{ type: "spring", stiffness: 400, damping: 32 }}
              />
            )}
            <span className={`relative ${active ? "text-navy" : "text-gray-500 hover:text-navy"}`}>
              {label}
            </span>
          </Link>
        );
      })}
    </nav>
  );
}
