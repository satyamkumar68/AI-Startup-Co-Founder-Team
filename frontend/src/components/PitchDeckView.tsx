import React, { useState, useEffect } from 'react';
import type { PitchWriterOutput } from '../types';

interface Props {
  data?: PitchWriterOutput | null;
}

export const PitchDeckView: React.FC<Props> = ({ data }) => {
  const [currentSlideIndex, setCurrentSlideIndex] = useState(0);
  const [viewMode, setViewMode] = useState<'carousel' | 'grid'>('carousel');
  const [showSpeakerNotes, setShowSpeakerNotes] = useState(true);

  if (!data || !data.slides || data.slides.length === 0) {
    return <div style={{ color: 'var(--text-muted)', padding: '24px' }}>Pitch deck is being composed...</div>;
  }

  const slides = data.slides;
  const currentSlide = slides[currentSlideIndex] || slides[0];

  const handlePrev = () => {
    setCurrentSlideIndex((prev) => (prev > 0 ? prev - 1 : slides.length - 1));
  };

  const handleNext = () => {
    setCurrentSlideIndex((prev) => (prev < slides.length - 1 ? prev + 1 : 0));
  };

  // Keyboard navigation for presentation mode
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't intercept if user is typing into an input/textarea
      const tag = (e.target as HTMLElement)?.tagName?.toLowerCase();
      if (tag === 'input' || tag === 'textarea') return;

      if (viewMode === 'carousel') {
        if (e.key === 'ArrowRight' || e.key === 'PageDown' || e.key === ' ') {
          e.preventDefault();
          setCurrentSlideIndex((prev) => (prev < slides.length - 1 ? prev + 1 : 0));
        } else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
          e.preventDefault();
          setCurrentSlideIndex((prev) => (prev > 0 ? prev - 1 : slides.length - 1));
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [viewMode, slides.length]);

  return (
    <div className="pitch-deck-container" id="pitch-deck-container">
      {/* Top Toolbar */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '20px',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span className="badge badge-primary">Pitch presentation</span>
          <span style={{ fontSize: '0.84rem', color: 'var(--text-muted)' }}>
            {slides.length} slides · Use ← / → to navigate
          </span>
        </div>

        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          {viewMode === 'carousel' && (
            <button
              id="btn-pitch-toggle-notes"
              type="button"
              className={`btn ${showSpeakerNotes ? 'btn-secondary' : 'btn-ghost'}`}
              onClick={() => setShowSpeakerNotes((prev) => !prev)}
              style={{ padding: '6px 12px', fontSize: '0.82rem' }}
              title="Toggle speaker script and talking points"
            >
              🎙️ {showSpeakerNotes ? 'Hide notes' : 'Show notes'}
            </button>
          )}

          <button
            id="btn-pitch-view-carousel"
            type="button"
            className={`btn ${viewMode === 'carousel' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setViewMode('carousel')}
            style={{ padding: '6px 12px', fontSize: '0.82rem' }}
          >
            Presentation view
          </button>
          <button
            id="btn-pitch-view-grid"
            type="button"
            className={`btn ${viewMode === 'grid' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setViewMode('grid')}
            style={{ padding: '6px 12px', fontSize: '0.82rem' }}
          >
            Grid overview
          </button>
        </div>
      </div>

      {viewMode === 'carousel' ? (
        <div>
          {/* Main 16:9 Presentation Canvas */}
          <div style={{
            position: 'relative',
            width: '100%',
            aspectRatio: '16 / 9',
            maxHeight: '480px',
            background: 'var(--glass-bg)',
            backdropFilter: 'blur(16px)',
            WebkitBackdropFilter: 'blur(16px)',
            border: '1px solid var(--glass-border)',
            boxShadow: 'var(--shadow-glow)',
            borderRadius: 'var(--radius-lg)',
            padding: '36px 44px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            overflow: 'hidden',
            transition: 'all 0.25s ease'
          }}>
            {/* Slide Header */}
            <div>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '16px'
              }}>
                <span style={{
                  fontSize: '0.8rem',
                  color: 'var(--cyan)',
                  fontWeight: 600,
                  letterSpacing: '0.04em',
                  textTransform: 'uppercase'
                }}>
                  Slide {currentSlideIndex + 1} of {slides.length}
                </span>
                <span style={{
                  fontSize: '0.74rem',
                  padding: '3px 8px',
                  borderRadius: '12px',
                  background: 'var(--bg-subtle)',
                  border: '1px solid var(--border)',
                  color: 'var(--text-muted)'
                }}>
                  Interactive Preview
                </span>
              </div>

              <h2 style={{
                fontFamily: 'var(--font-display)',
                fontSize: '1.75rem',
                fontWeight: 600,
                color: 'var(--text-main)',
                lineHeight: '1.3',
                marginBottom: '20px'
              }}>
                {currentSlide.title}
              </h2>
            </div>

            {/* Slide Bullets */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', flexGrow: 1 }}>
              {(currentSlide.bullets || []).map((bullet, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '12px',
                    fontSize: '1rem',
                    color: 'var(--text-main)',
                    lineHeight: '1.5'
                  }}
                >
                  <span style={{
                    width: '7px',
                    height: '7px',
                    borderRadius: '50%',
                    background: 'var(--primary)',
                    boxShadow: '0 0 6px var(--primary)',
                    marginTop: '9px',
                    flexShrink: 0
                  }} />
                  <span>{bullet}</span>
                </div>
              ))}
            </div>

            {/* Slide Footer */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              borderTop: '1px solid var(--border)',
              paddingTop: '12px',
              marginTop: '16px'
            }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Investor presentation · Autonomous Output
              </span>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>
                {currentSlideIndex + 1} / {slides.length}
              </span>
            </div>
          </div>

          {/* Carousel Controls */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginTop: '16px',
            marginBottom: '20px'
          }}>
            <button
              id="btn-pitch-prev"
              type="button"
              className="btn btn-secondary"
              onClick={handlePrev}
            >
              ← Previous slide
            </button>

            {/* Slide dot indicators */}
            <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
              {slides.map((_, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setCurrentSlideIndex(idx)}
                  style={{
                    width: idx === currentSlideIndex ? '24px' : '7px',
                    height: '7px',
                    borderRadius: '4px',
                    background: idx === currentSlideIndex ? 'var(--primary)' : 'var(--border)',
                    boxShadow: idx === currentSlideIndex ? 'var(--shadow-glow)' : 'none',
                    border: 'none',
                    cursor: 'pointer',
                    transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)'
                  }}
                  title={`Go to slide ${idx + 1}: ${slides[idx].title}`}
                />
              ))}
            </div>

            <button
              id="btn-pitch-next"
              type="button"
              className="btn btn-primary"
              onClick={handleNext}
            >
              Next slide →
            </button>
          </div>

          {/* Speaker Notes Script */}
          {showSpeakerNotes && (
            <div style={{
              background: 'var(--glass-bg)',
              backdropFilter: 'blur(12px)',
              WebkitBackdropFilter: 'blur(12px)',
              border: '1px solid var(--glass-border)',
              borderRadius: 'var(--radius-md)',
              padding: '18px 20px',
              transition: 'all 0.2s ease'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <span style={{ fontSize: '0.9rem' }}>🎙️</span>
                <h4 style={{ fontSize: '0.84rem', color: 'var(--warning)', fontWeight: 600, margin: 0 }}>
                  Speaker script and talking points
                </h4>
              </div>
              <p style={{
                color: 'var(--text-main)',
                fontSize: '0.9rem',
                lineHeight: '1.6',
                fontStyle: 'italic',
                whiteSpace: 'pre-line'
              }}>
                "{currentSlide.speaker_notes}"
              </p>
            </div>
          )}
        </div>
      ) : (
        /* Grid Overview */
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
          gap: '16px'
        }}>
          {slides.map((slide, idx) => (
            <div
              key={idx}
              onClick={() => {
                setCurrentSlideIndex(idx);
                setViewMode('carousel');
              }}
              style={{
                background: idx === currentSlideIndex ? 'rgba(79, 70, 229, 0.08)' : 'var(--bg-subtle)',
                border: idx === currentSlideIndex ? '1px solid var(--primary)' : '1px solid var(--border)',
                boxShadow: idx === currentSlideIndex ? 'var(--shadow-glow)' : 'none',
                borderRadius: 'var(--radius-md)',
                padding: '16px',
                cursor: 'pointer',
                transition: 'all 0.18s ease',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="badge badge-info" style={{ fontSize: '0.72rem' }}>
                  Slide {idx + 1}
                </span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-subtle)' }}>
                  {slide.bullets.length} points
                </span>
              </div>
              <h4 style={{ color: 'var(--text-main)', fontSize: '0.92rem', fontWeight: 600, minHeight: '36px' }}>
                {slide.title}
              </h4>
              <p style={{
                color: 'var(--text-muted)',
                fontSize: '0.8rem',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                display: '-webkit-box',
                WebkitLineClamp: 2,
                WebkitBoxOrient: 'vertical'
              }}>
                {slide.bullets[0]}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
