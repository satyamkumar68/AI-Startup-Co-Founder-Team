import React, { useState } from 'react';
import type { PitchWriterOutput } from '../types';

interface Props {
  data?: PitchWriterOutput | null;
}

export const PitchDeckView: React.FC<Props> = ({ data }) => {
  const [currentSlideIndex, setCurrentSlideIndex] = useState(0);
  const [viewMode, setViewMode] = useState<'carousel' | 'grid'>('carousel');

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

  return (
    <div className="pitch-deck-container" id="pitch-deck-container">
      {/* Top Toolbar */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '20px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span className="badge badge-primary">Pitch presentation</span>
          <span style={{ fontSize: '0.84rem', color: 'var(--text-muted)' }}>
            {slides.length} slides
          </span>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
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
            background: 'var(--bg-subtle)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-lg)',
            padding: '36px 44px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            overflow: 'hidden'
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
                  fontWeight: 500
                }}>
                  Slide {currentSlideIndex + 1} of {slides.length}
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
                    color: '#E2E8F0',
                    lineHeight: '1.5'
                  }}
                >
                  <span style={{
                    width: '6px',
                    height: '6px',
                    borderRadius: '50%',
                    background: 'var(--primary)',
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
                Investor presentation
              </span>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
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
              Previous slide
            </button>

            {/* Slide dot indicators */}
            <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
              {slides.map((_, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setCurrentSlideIndex(idx)}
                  style={{
                    width: idx === currentSlideIndex ? '20px' : '6px',
                    height: '6px',
                    borderRadius: '3px',
                    background: idx === currentSlideIndex ? 'var(--primary)' : 'var(--border)',
                    border: 'none',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                  title={`Go to slide ${idx + 1}`}
                />
              ))}
            </div>

            <button
              id="btn-pitch-next"
              type="button"
              className="btn btn-primary"
              onClick={handleNext}
            >
              Next slide
            </button>
          </div>

          {/* Speaker Notes Script */}
          <div style={{
            background: 'var(--bg-subtle)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-md)',
            padding: '18px 20px'
          }}>
            <h4 style={{ fontSize: '0.82rem', color: 'var(--warning)', fontWeight: 600, marginBottom: '6px' }}>
              Speaker script and talking points
            </h4>
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
                borderRadius: 'var(--radius-md)',
                padding: '16px',
                cursor: 'pointer',
                transition: 'border-color 0.15s ease',
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
