import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer className="border-t border-border mt-24">
      <div className="container flex flex-col md:flex-row items-start md:items-center justify-between gap-3 py-8 text-sm text-muted-foreground">
        <p className="font-mono text-xs">Built for Digital Image Processing project · 2026</p>
        <Link to="/demo" className="text-foreground hover:text-primary transition-colors">
          Open demo →
        </Link>
      </div>
    </footer>
  );
}
