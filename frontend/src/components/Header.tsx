import { Link, NavLink, useLocation } from "react-router-dom";
import { Moon, Sun, ScanLine } from "lucide-react";
import { useEffect, useState } from "react";
import { useDarkMode } from "@/hooks/useDarkMode";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

export default function Header() {
  const { theme, toggle } = useDarkMode();
  const [count, setCount] = useState<number | null>(null);
  const location = useLocation();

  useEffect(() => {
    let alive = true;
    api
      .listPlates(1, 0)
      .then((r) => {
        // Some backends return a total separately; here we only know we got at least N.
        // We'll re-fetch up to 1000 to estimate.
        return api.listPlates(1000, 0).then((full) => {
          if (alive) setCount(full.plates.length);
        });
      })
      .catch(() => {
        if (alive) setCount(null);
      });
    return () => {
      alive = false;
    };
  }, [location.pathname]);

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur">
      <div className="container flex h-16 items-center justify-between">
        <Link to="/" className="flex items-center gap-2.5 group">
          <span className="flex h-8 w-8 items-center justify-center rounded-md border border-border bg-card">
            <ScanLine className="h-4 w-4 text-primary" strokeWidth={2} />
          </span>
          <div className="flex flex-col leading-none">
            <span className="text-sm font-semibold tracking-tight">PlateScan</span>
            <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
              LPR · DIP
            </span>
          </div>
        </Link>

        <nav className="flex items-center gap-1">
          <NavItem to="/">Overview</NavItem>
          <NavItem to="/demo">Demo</NavItem>
          {count !== null && (
            <span className="ml-3 hidden md:inline-flex items-center gap-1.5 font-mono text-xs text-muted-foreground">
              <span className="h-1.5 w-1.5 rounded-full bg-primary" />
              {count} reads
            </span>
          )}
          <button
            onClick={toggle}
            aria-label="Toggle theme"
            className="ml-2 inline-flex h-9 w-9 items-center justify-center rounded-md border border-border text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
          >
            {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
        </nav>
      </div>
    </header>
  );
}

function NavItem({ to, children }: { to: string; children: React.ReactNode }) {
  return (
    <NavLink
      to={to}
      end
      className={({ isActive }) =>
        cn(
          "px-3 py-1.5 text-sm rounded-md transition-colors",
          isActive ? "text-primary font-medium" : "text-muted-foreground hover:text-foreground"
        )
      }
    >
      {children}
    </NavLink>
  );
}
