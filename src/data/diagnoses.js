// Справочник диагнозов для отображения (как в прототипе CAS_ISIC)
export const DIAGNOSES = {
  melanoma: {
    name: 'Меланома',
    malignant: true,
    description: 'Наиболее опасная форма рака кожи',
  },
  nevus: {
    name: 'Невус (родинка)',
    malignant: false,
    description: 'Обычная родинка, неопасна',
  },
  bcc: {
    name: 'Базальноклеточная карцинома',
    malignant: true,
    description: 'Самая распространенная форма рака кожи',
  },
  seborrheic_keratosis: {
    name: 'Себорейный кератоз',
    malignant: false,
    description: 'Доброкачественное новообразование кожи',
  },
  actinic_keratosis: {
    name: 'Актинический кератоз',
    malignant: false,
    description: 'Предраковое изменение кожи',
  },
}

// Имитация ответа модели: возвращает топ-3 и основной диагноз
export function mockAnalyze() {
  const keys = Object.keys(DIAGNOSES)
  const count = 3
  const chosen = []
  const remaining = [...keys]
  for (let i = 0; i < count; i++) {
    const idx = Math.floor(Math.random() * remaining.length)
    chosen.push(remaining.splice(idx, 1)[0])
  }
  let total = 100
  const probabilities = chosen.map((key, i) => {
    const value = i === 0 ? 50 + Math.floor(Math.random() * 50) : Math.floor(Math.random() * (total - 1))
    total -= value
    return { key, value: Math.max(0.01, value) }
  })
  if (total > 0) probabilities[probabilities.length - 1].value += total
  const sum = probabilities.reduce((s, p) => s + p.value, 0)
  probabilities.forEach(p => { p.value = Math.round((p.value / sum) * 10000) / 100 })
  return {
    main: probabilities[0],
    top3: probabilities,
  }
}
