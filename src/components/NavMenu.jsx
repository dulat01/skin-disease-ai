import React from 'react'
import { NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './NavMenu.css'

export default function NavMenu() {
  const { user } = useAuth()

  const links = [
    { to: '/', label: 'Главная', end: true },
    { to: '/history', label: 'История', end: false },
    { to: '/settings', label: 'Настройки', end: false },
    ...(user?.isAdmin ? [{ to: '/admin', label: 'Админ', end: false }] : []),
  ]

  return (
    <nav className="nav-menu" aria-label="Главное меню">
      <ul className="nav-menu-list">
        {links.map(({ to, label, end }) => (
          <li key={to}>
            <NavLink
              to={to}
              end={end}
              className={({ isActive }) => `nav-menu-link ${isActive ? 'nav-menu-link-active' : ''}`}
            >
              {label}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  )
}
