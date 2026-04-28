import React from 'react'
import { Outlet } from 'react-router-dom'
import Header from './Header'
import NavMenu from './NavMenu'
import './Layout.css'

export default function Layout() {
  return (
    <div className="layout">
      <Header />
      <NavMenu />
      <main className="layout-main">
        <Outlet />
      </main>
    </div>
  )
}
