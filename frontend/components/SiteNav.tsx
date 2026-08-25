"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";

const NAV_LINKS = [
  { href: "/", label: "New Campaign" },
  { href: "/calendar", label: "Calendar" },
  { href: "/profiles", label: "Profiles" },
];

/**
 * Top nav with a sliding active-link pill — the same Framer Motion
 * layoutId shared-layout technique used for the Profiles page's card
 * expand, applied to a simpler case: one highlight element that glides
 * from the previous active link to the new one on navigation, instead of
 * an instant on/off state change.
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
                className="absolute inset-0 rounded-md bg-white/15"
                transition={{ type: "spring", stiffness: 400, damping: 32 }}
              />
            )}
            <span className={`relative ${active ? "text-white" : "text-white/80 hover:text-white"}`}>
              {label}
            </span>
          </Link>
        );
      })}
    </nav>
  );
}
