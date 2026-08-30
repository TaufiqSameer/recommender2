import type { ReactNode } from "react";
import Sidebar from "./Sidebar";
import { useAuth } from "../context/AuthContext";

export default function Layout({ children }: { children: ReactNode }) {
  const { user } = useAuth();

  const initials = (user?.display_name ?? user?.username ?? "L")
    .charAt(0)
    .toUpperCase();

  return (
    <div className="app-shell">
      <Sidebar />
      <div className="main-wrapper">
        <header className="topbar">
          <div />
          <div className="profile">
            <div className="profile-avatar">{initials}</div>
            <div>
              <p className="profile-name">{user?.display_name ?? user?.username}</p>
              <p className="profile-role">Learner</p>
            </div>
          </div>
        </header>
        <main className="main-content">
          {children}
        </main>
      </div>
    </div>
  );
}
