import { NavLink, useNavigate } from "react-router-dom";
import {
  BarChart3,
  BookOpen,
  Clock3,
  LayoutDashboard,
  LogOut,
  Map,
  Settings,
  UserCircle,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";

const NAV_ITEMS = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard", end: true },
  { to: "/learn", icon: BookOpen, label: "Learn" },
  { to: "/roadmap", icon: Map, label: "Roadmap" },
  { to: "/progress", icon: BarChart3, label: "Progress" },
  { to: "/history", icon: Clock3, label: "History" },
];

const BOTTOM_ITEMS = [
  { to: "/profile", icon: UserCircle, label: "Profile" },
  { to: "/settings", icon: Settings, label: "Settings" },
];

export default function Sidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  const initials = (user?.display_name ?? user?.username ?? "L")
    .charAt(0)
    .toUpperCase();

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">L</div>
        <span className="brand-name">LearnAI</span>
      </div>

      <nav className="sidebar-nav">
        {NAV_ITEMS.map(({ to, icon: Icon, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `nav-item${isActive ? " active" : ""}`
            }
          >
            <Icon size={19} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-bottom">
        {BOTTOM_ITEMS.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `nav-item${isActive ? " active" : ""}`
            }
          >
            <Icon size={19} />
            <span>{label}</span>
          </NavLink>
        ))}

        <div className="sidebar-user">
          <div className="sidebar-avatar">{initials}</div>
          <div className="sidebar-user-info">
            <p className="sidebar-username">{user?.display_name ?? user?.username}</p>
            <p className="sidebar-email">{user?.email}</p>
          </div>
        </div>

        <button className="nav-item nav-logout" onClick={handleLogout}>
          <LogOut size={19} />
          <span>Logout</span>
        </button>
      </div>
    </aside>
  );
}
