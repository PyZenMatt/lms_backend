import { NavLink } from "react-router-dom";

export default function NavItem({ to, children }: { to: string; children: React.ReactNode }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        [
          "px-3 py-1.5 rounded-md text-sm",
          isActive ? "bg-secondary text-secondary-foreground" : "hover:bg-accent hover:text-accent-foreground",
        ].join(" ")
      }
    >
      {children}
    </NavLink>
  );
}
