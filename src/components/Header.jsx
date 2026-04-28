import React from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './Header.css'

export default function Header() {
  const { user, logout } = useAuth()

  return (
    <header className="header">
      <div className="header-inner">
        <div className="header-brand">
          <Link to="/" className="header-brand-link">
            <span className="header-icon" aria-hidden>✚</span>
            <div>
              <h1 className="header-title">ДИАГНОСТИКА ЗАБОЛЕВАНИЙ КОЖИ</h1>
              <p className="header-subtitle">ResNet18 | Точность: 77.10% | CAS_ISIC Adapted</p>
            </div>
          </Link>
        </div>
        <nav className="header-actions">
          <span className="header-user">{user?.name || user?.email}</span>
          <button type="button" className="header-logout" onClick={logout}>
            Выйти
          </button>
        </nav>
      </div>
    </header>
  )
}
