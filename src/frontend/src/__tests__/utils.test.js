import { describe, it, expect } from 'vitest'

// Test utility functions that could be extracted from components

describe('Data formatting utilities', () => {
  describe('salary formatting', () => {
    it('should format Colombian pesos correctly', () => {
      const formatCOP = (n) => {
        if (!n) return 'No especificado'
        return `$${n.toLocaleString('es-CO')}`
      }
      expect(formatCOP(1300000)).toContain('1')
      expect(formatCOP(null)).toBe('No especificado')
      expect(formatCOP(0)).toBe('No especificado')
    })
  })

  describe('DANE code validation', () => {
    it('should validate known DANE codes', () => {
      const VALID_DANE = ['05045', '05837', '05147', '05172', '05490',
        '05665', '05659', '05051', '05480', '05475', '05873']
      const isValidDane = (code) => VALID_DANE.includes(code)

      expect(isValidDane('05045')).toBe(true)  // Apartadó
      expect(isValidDane('05837')).toBe(true)  // Turbo
      expect(isValidDane('99999')).toBe(false)
    })
  })

  describe('municipio name normalization', () => {
    it('should match municipios case-insensitively', () => {
      const normalize = (s) => s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')
      expect(normalize('Apartadó')).toBe('apartado')
      expect(normalize('TURBO')).toBe('turbo')
      expect(normalize('Chigorodó')).toBe('chigorodo')
    })
  })
})
