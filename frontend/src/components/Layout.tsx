import { NavLink, Outlet } from "react-router-dom";
import { SYSTEMS } from "../systems";

function navClass({ isActive }: { isActive: boolean }): string {
  return isActive ? "nav-link active" : "nav-link";
}

export function Layout() {
  return (
    <div className="shell">
      <aside className="sidebar">
        <NavLink to="/" className="brand" end>
          <span className="mark" aria-hidden="true">
            M
          </span>
          <strong>MedBud</strong>
        </NavLink>
        <nav className="nav" aria-label="Prediction systems">
          <NavLink to="/" end className={navClass}>
            Overview
          </NavLink>
          {SYSTEMS.map((item) => (
            <NavLink key={item.id} to={item.href} className={navClass}>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <p className="side-note">Not a diagnosis.</p>
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
