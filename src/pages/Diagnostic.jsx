import React, { useState, useRef } from 'react'
import { useAuth } from '../context/AuthContext'
import { DIAGNOSES, mockAnalyze } from '../data/diagnoses'
import { addToHistory } from '../data/history'
import './Diagnostic.css'

export default function Diagnostic() {
  const { user } = useAuth()
  const [image, setImage] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const fileInputRef = useRef(null)

  const handleFile = (e) => {
    const file = e.target.files?.[0]
    if (!file || !file.type.startsWith('image/')) return
    const reader = new FileReader()
    reader.onload = () => {
      const dataUrl = reader.result
      setImage(dataUrl)
      setResult(null)
      setLoading(true)
      setTimeout(() => {
        const analysis = mockAnalyze()
        setResult(analysis)
        if (user?.email) {
          addToHistory(user.email, { result: analysis, image: dataUrl })
        }
        setLoading(false)
      }, 800)
    }
    reader.readAsDataURL(file)
  }

  const handleUploadClick = () => fileInputRef.current?.click()

  const reset = () => {
    setImage(null)
    setResult(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  return (
    <div className="diagnostic">
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFile}
        className="diagnostic-input-hidden"
        aria-label="Выбрать изображение"
      />

      {!image ? (
        <div className="diagnostic-upload-area">
          <button type="button" className="diagnostic-upload-btn" onClick={handleUploadClick}>
            <span className="diagnostic-upload-icon">📷</span>
            ЗАГРУЗИТЬ ИЗОБРАЖЕНИЕ
          </button>
        </div>
      ) : (
        <div className="diagnostic-results">
          <div className="diagnostic-image-block">
            <h3 className="diagnostic-block-title">Анализируемое изображение</h3>
            <div className="diagnostic-image-wrap">
              {loading ? (
                <div className="diagnostic-loading">
                  <span className="diagnostic-spinner" />
                  Анализ изображения...
                </div>
              ) : (
                <img src={image} alt="Загруженное изображение кожи" className="diagnostic-image" />
              )}
            </div>
            <button type="button" className="diagnostic-reset" onClick={reset}>
              Загрузить другое
            </button>
          </div>

          {result && !loading && (
            <div className="diagnostic-diagnosis-block">
              <h3 className="diagnostic-block-title">ОСНОВНОЙ ДИАГНОЗ</h3>
              {(() => {
                const main = result.main
                const info = DIAGNOSES[main.key]
                if (!info) return null
                return (
                  <div className="diagnostic-main">
                    <div className="diagnostic-main-name">{info.name}</div>
                    <div className={`diagnostic-badge ${info.malignant ? 'diagnostic-badge-malignant' : 'diagnostic-badge-benign'}`}>
                      {info.malignant ? <span className="diagnostic-badge-dot" /> : <span className="diagnostic-badge-check">✓</span>}
                      {info.malignant ? 'ЗЛОКАЧЕСТВЕННАЯ' : 'ДОБРОКАЧЕСТВЕННАЯ'}
                    </div>
                    <div className="diagnostic-confidence">Уверенность: {main.value}%</div>
                    <p className="diagnostic-description">{info.description}</p>
                  </div>
                )
              })()}

              <h3 className="diagnostic-block-title diagnostic-top3-title">ТОП-3 ВЕРОЯТНОСТИ</h3>
              <ul className="diagnostic-top3">
                {result.top3.map((item, index) => {
                  const info = DIAGNOSES[item.key]
                  if (!info) return null
                  return (
                    <li key={item.key} className="diagnostic-top3-item">
                      <div className="diagnostic-top3-label">
                        {index + 1}. {info.name}: {item.value}%
                      </div>
                      <div className="diagnostic-top3-bar-wrap">
                        <div
                          className={`diagnostic-top3-bar ${index === 0 ? 'diagnostic-top3-bar-first' : ''}`}
                          style={{ width: `${item.value}%` }}
                        />
                      </div>
                    </li>
                  )
                })}
              </ul>
            </div>
          )}
        </div>
      )}

      <div className="diagnostic-disclaimer">
        <span className="diagnostic-disclaimer-icon" aria-hidden>⚠</span>
        ВНИМАНИЕ. Это только помощь в диагностике! Всегда консультируйтесь с врачом-дерматологом!
      </div>
    </div>
  )
}
