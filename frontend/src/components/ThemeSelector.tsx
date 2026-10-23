import { useEffect, useState, useRef } from 'react';

export type ThemeMode =
  | 'midnight'
  | 'classic'
  | 'slate'
  | 'emerald'
  | 'cyberpunk'
  | 'amber'
  | 'porcelain';

export interface ThemeDefinition {
  id: ThemeMode;
  label: string;
  hint: string;
  category: 'dark' | 'light';
  palette: [string, string, string, string]; // [canvas, surface, primary, accent]
}

export const THEMES: ThemeDefinition[] = [
  // Dark & Futuristic
  {
    id: 'midnight',
    label: 'Midnight Studio',
    hint: 'Dark space indigo studio',
    category: 'dark',
    palette: ['#0B0F17', '#141B26', '#4F46E5', '#0EA5E9']
  },
  {
    id: 'emerald',
    label: 'Emerald Growth',
    hint: 'Fintech & wealth velvet forest',
    category: 'dark',
    palette: ['#061A14', '#0D2B22', '#10B981', '#2DD4BF']
  },
  {
    id: 'cyberpunk',
    label: 'Cyberpunk Neon',
    hint: 'Tokyo abyss & violet matrix',
    category: 'dark',
    palette: ['#090814', '#131126', '#8B5CF6', '#06B6D4']
  },
  {
    id: 'slate',
    label: 'Nordic Slate',
    hint: 'Cool steel monochrome',
    category: 'dark',
    palette: ['#0F172A', '#1E293B', '#0284C7', '#38BDF8']
  },
  {
    id: 'amber',
    label: 'Sunset Amber',
    hint: 'Smoked ember & warm copper',
    category: 'dark',
    palette: ['#140F0D', '#201915', '#F59E0B', '#FB923C']
  },
  // Light & Editorial
  {
    id: 'porcelain',
    label: 'Porcelain Crisp',
    hint: 'Modern Linear-style clean light',
    category: 'light',
    palette: ['#F8FAFC', '#FFFFFF', '#2563EB', '#0284C7']
  },
  {
    id: 'classic',
    label: 'Classic Ink',
    hint: 'Warm editorial ivory & serif',
    category: 'light',
    palette: ['#FAF7F2', '#FFFFFF', '#8B3A2B', '#5E5850']
  }
];

interface ThemeSelectorProps {
  className?: string;
}

export function ThemeSelector({ className = '' }: ThemeSelectorProps) {
  const [theme, setTheme] = useState<ThemeMode>(() => {
    try {
      const saved = localStorage.getItem('co_founder_theme') as ThemeMode | null;
      if (saved && THEMES.some((t) => t.id === saved)) {
        return saved;
      }
    } catch {
      // ignore localStorage errors
    }
    return 'midnight';
  });

  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    try {
      localStorage.setItem('co_founder_theme', theme);
    } catch {
      // ignore
    }
    // Broadcast theme change for dynamic canvas listeners (e.g. Mermaid, SVG graphs)
    window.dispatchEvent(new CustomEvent('co_founder_theme_change', { detail: { theme } }));
  }, [theme]);

  // Click outside listener to dismiss popover
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleKeyDown);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen]);

  const activeThemeObj = THEMES.find((t) => t.id === theme) || THEMES[0];
  const darkThemes = THEMES.filter((t) => t.category === 'dark');
  const lightThemes = THEMES.filter((t) => t.category === 'light');

  const handleSelectTheme = (id: ThemeMode) => {
    setTheme(id);
    setIsOpen(false);
  };

  return (
    <div
      ref={containerRef}
      className={`theme-selector-container ${className}`}
      title="Customize workspace visual palette and typography"
    >
      {/* Trigger Button with live dual-color swatch preview */}
      <button
        type="button"
        id="btn-theme-selector-trigger"
        className={`theme-trigger-btn ${isOpen ? 'open' : ''}`}
        onClick={() => setIsOpen((prev) => !prev)}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
      >
        <span className="theme-swatch-duo">
          <span
            className="swatch-base"
            style={{ backgroundColor: activeThemeObj.palette[0] }}
          />
          <span
            className="swatch-accent-dot"
            style={{ backgroundColor: activeThemeObj.palette[2] }}
          />
        </span>
        <span className="theme-active-label">{activeThemeObj.label}</span>
        <span className="theme-chevron">▼</span>
      </button>

      {/* Glassmorphic Dropdown Popover */}
      {isOpen && (
        <div
          className="theme-dropdown-popover"
          role="listbox"
          aria-label="Select visual workspace theme"
        >
          {/* Dark & Futuristic Section */}
          <div className="theme-dropdown-header">Dark & Neon Labs</div>
          {darkThemes.map((t) => {
            const isSelected = theme === t.id;
            return (
              <button
                key={t.id}
                type="button"
                className={`theme-dropdown-item ${isSelected ? 'active' : ''}`}
                onClick={() => handleSelectTheme(t.id)}
                role="option"
                aria-selected={isSelected}
              >
                <div className="theme-item-left">
                  <div className="theme-palette-dots">
                    {t.palette.map((color, idx) => (
                      <span
                        key={idx}
                        className="palette-dot"
                        style={{ backgroundColor: color }}
                      />
                    ))}
                  </div>
                  <div className="theme-item-info">
                    <span className="theme-item-name">{t.label}</span>
                    <span className="theme-item-desc">{t.hint}</span>
                  </div>
                </div>
                {isSelected && <span className="theme-active-check">✓</span>}
              </button>
            );
          })}

          <div className="theme-dropdown-divider" />

          {/* Light & Editorial Section */}
          <div className="theme-dropdown-header">Light & Editorial</div>
          {lightThemes.map((t) => {
            const isSelected = theme === t.id;
            return (
              <button
                key={t.id}
                type="button"
                className={`theme-dropdown-item ${isSelected ? 'active' : ''}`}
                onClick={() => handleSelectTheme(t.id)}
                role="option"
                aria-selected={isSelected}
              >
                <div className="theme-item-left">
                  <div className="theme-palette-dots">
                    {t.palette.map((color, idx) => (
                      <span
                        key={idx}
                        className="palette-dot"
                        style={{ backgroundColor: color }}
                      />
                    ))}
                  </div>
                  <div className="theme-item-info">
                    <span className="theme-item-name">{t.label}</span>
                    <span className="theme-item-desc">{t.hint}</span>
                  </div>
                </div>
                {isSelected && <span className="theme-active-check">✓</span>}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
