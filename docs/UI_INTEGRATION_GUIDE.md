# Adaptive FHRI UI Integration Guide

## Overview

This guide shows how to integrate the Adaptive FHRI visual indicators into your frontend UI.

## Response Schema

The `/ask` endpoint now returns enhanced metadata when `use_adaptive_fhri=true`:

```json
{
  "answer": "Apple stock is trading at $150.23...",
  "meta": {
    "fhri": 0.712,
    "fhri_label": "High Reliability",
    "fhri_weights": {
      "entropy": 0.25,
      "contradiction": 0.20,
      "grounding": 0.25,
      "numeric": 0.20,
      "temporal": 0.10
    },
    "contradiction_smoothed": 0.35,
    "stability_index": 0.82,
    "fhri_warnings": [],
    "fhri_total_turns": 15,
    "fhri_window_size": 10
  }
}
```

## Visual Components

### 1. FHRI Badge with Trend Sparkline

Display FHRI score with color-coded badge and mini trend chart.

```jsx
// React component example
import { Sparklines, SparklinesLine } from 'react-sparklines';

function FHRIBadge({ fhri, fhriLabel, fhriHistory = [] }) {
  const getColor = (score) => {
    if (score >= 0.75) return '#22c55e'; // Green
    if (score >= 0.50) return '#eab308'; // Yellow
    if (score >= 0.30) return '#f97316'; // Orange
    return '#ef4444'; // Red
  };

  return (
    <div className="flex items-center gap-2">
      {/* FHRI Badge */}
      <span
        className="px-3 py-1 rounded-full text-sm font-semibold"
        style={{
          backgroundColor: getColor(fhri),
          color: 'white'
        }}
      >
        {fhriLabel} ({(fhri * 100).toFixed(0)}%)
      </span>

      {/* Sparkline Trend */}
      {fhriHistory.length > 3 && (
        <div className="w-16 h-8">
          <Sparklines data={fhriHistory} width={64} height={32}>
            <SparklinesLine color={getColor(fhri)} />
          </Sparklines>
        </div>
      )}
    </div>
  );
}
```

### 2. Stability Indicator

Show stability index with visual gauge.

```jsx
function StabilityIndicator({ stabilityIndex }) {
  const getStabilityColor = (index) => {
    if (index >= 0.9) return '#22c55e';
    if (index >= 0.7) return '#eab308';
    return '#f97316';
  };

  const percentage = Math.round(stabilityIndex * 100);

  return (
    <div className="flex items-center gap-2">
      <span className="text-sm text-gray-600">Stability:</span>

      {/* Progress bar */}
      <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="h-full transition-all"
          style={{
            width: `${percentage}%`,
            backgroundColor: getStabilityColor(stabilityIndex)
          }}
        />
      </div>

      <span className="text-xs font-medium">{percentage}%</span>
    </div>
  );
}
```

### 3. Warnings Display

Show FHRI warnings with icons.

```jsx
function FHRIWarnings({ warnings }) {
  if (!warnings || warnings.length === 0) return null;

  return (
    <div className="mt-2 space-y-1">
      {warnings.map((warning, idx) => (
        <div key={idx} className="flex items-start gap-2 text-sm text-amber-600">
          <svg className="w-4 h-4 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          <span>{warning}</span>
        </div>
      ))}
    </div>
  );
}
```

### 4. Component Breakdown Tooltip

Show detailed weight breakdown on hover.

```jsx
function FHRITooltip({ fhri, fhriWeights, subscores }) {
  const components = [
    { name: 'Grounding', key: 'grounding', icon: '📚' },
    { name: 'Numeric', key: 'numeric', icon: '🔢' },
    { name: 'Entropy', key: 'entropy', icon: '🎲' },
    { name: 'Contradiction', key: 'contradiction', icon: '⚖️' },
    { name: 'Temporal', key: 'temporal', icon: '⏰' }
  ];

  return (
    <div className="p-3 bg-white shadow-lg rounded-lg border border-gray-200 text-sm">
      <div className="font-semibold mb-2">FHRI Breakdown</div>

      {components.map(({ name, key, icon }) => {
        const weight = fhriWeights[key];
        const score = subscores[key];
        const contribution = weight * score;

        return (
          <div key={key} className="flex items-center gap-2 py-1">
            <span>{icon}</span>
            <span className="flex-1">{name}</span>
            <span className="text-gray-600">{(weight * 100).toFixed(0)}%</span>
            <span className="font-mono text-xs">
              {score?.toFixed(2) ?? 'N/A'}
            </span>
            <span className="text-green-600 font-medium">
              +{(contribution * 100).toFixed(0)}
            </span>
          </div>
        );
      })}

      <div className="border-t border-gray-200 mt-2 pt-2">
        <div className="flex justify-between font-semibold">
          <span>Total FHRI:</span>
          <span>{(fhri * 100).toFixed(0)}%</span>
        </div>
      </div>
    </div>
  );
}
```

## Complete Integration Example

```jsx
import { useState, useEffect } from 'react';

function ChatMessage({ message }) {
  const [fhriHistory, setFhriHistory] = useState([]);

  useEffect(() => {
    if (message.meta?.fhri) {
      setFhriHistory(prev => [...prev, message.meta.fhri].slice(-10));
    }
  }, [message.meta?.fhri]);

  return (
    <div className="chat-message">
      {/* Message content */}
      <div className="prose">
        {message.answer}
      </div>

      {/* FHRI metadata panel */}
      {message.meta?.fhri && (
        <div className="mt-4 p-3 bg-gray-50 rounded-lg space-y-2">
          {/* FHRI Badge with Sparkline */}
          <FHRIBadge
            fhri={message.meta.fhri}
            fhriLabel={message.meta.fhri_label}
            fhriHistory={fhriHistory}
          />

          {/* Stability Indicator */}
          <StabilityIndicator
            stabilityIndex={message.meta.stability_index}
          />

          {/* Warnings */}
          <FHRIWarnings
            warnings={message.meta.fhri_warnings}
          />

          {/* Details (expandable) */}
          <details className="text-sm">
            <summary className="cursor-pointer text-gray-600">
              Show FHRI Details
            </summary>
            <FHRITooltip
              fhri={message.meta.fhri}
              fhriWeights={message.meta.fhri_weights}
              subscores={message.meta.fhri_subscores}
            />
          </details>
        </div>
      )}
    </div>
  );
}
```

## Styling Recommendations

### Color Palette

```css
/* FHRI Score Colors */
.fhri-high {
  background-color: #22c55e; /* Green - High Reliability (≥75%) */
}

.fhri-medium {
  background-color: #eab308; /* Yellow - Medium Reliability (50-75%) */
}

.fhri-low {
  background-color: #f97316; /* Orange - Low Reliability (30-50%) */
}

.fhri-very-low {
  background-color: #ef4444; /* Red - Very Low Reliability (<30%) */
}

/* Stability Colors */
.stability-excellent {
  background-color: #22c55e; /* ≥90% */
}

.stability-good {
  background-color: #eab308; /* 70-90% */
}

.stability-moderate {
  background-color: #f97316; /* <70% */
}
```

### Animations

```css
/* Smooth transitions for FHRI changes */
.fhri-badge {
  transition: all 0.3s ease-in-out;
}

/* Pulse animation for warnings */
@keyframes pulse-warning {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.fhri-warning {
  animation: pulse-warning 2s infinite;
}

/* Sparkline container */
.fhri-sparkline {
  display: inline-block;
  vertical-align: middle;
  margin-left: 8px;
}
```

## Mobile Responsive Design

```jsx
function FHRIMobileCard({ fhri, fhriLabel, stabilityIndex, warnings }) {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      {/* Mobile-optimized layout */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs text-gray-600">Reliability</span>
        <span
          className="px-2 py-1 rounded text-xs font-semibold"
          style={{ backgroundColor: getColor(fhri), color: 'white' }}
        >
          {(fhri * 100).toFixed(0)}%
        </span>
      </div>

      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-600">Stability</span>
        <div className="flex items-center gap-2">
          <div className="w-16 h-1 bg-gray-200 rounded-full">
            <div
              className="h-full rounded-full"
              style={{
                width: `${stabilityIndex * 100}%`,
                backgroundColor: getStabilityColor(stabilityIndex)
              }}
            />
          </div>
          <span className="text-xs">{(stabilityIndex * 100).toFixed(0)}%</span>
        </div>
      </div>

      {warnings?.length > 0 && (
        <div className="mt-2 text-xs text-amber-600">
          ⚠ {warnings[0]}
        </div>
      )}
    </div>
  );
}
```

## API Request Example

```javascript
async function askQuestion(question, conversationHistory = []) {
  const response = await fetch('http://localhost:8000/ask', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      text: question,
      prev_assistant_turn: conversationHistory[conversationHistory.length - 1]?.answer,
      use_adaptive_fhri: true,  // Enable adaptive FHRI
      use_entropy: true,
      use_nli: true,
      use_realtime: true,
      use_crypto: true
    })
  });

  const data = await response.json();

  return {
    answer: data.answer,
    fhri: data.meta.fhri,
    fhriLabel: data.meta.fhri_label,
    stabilityIndex: data.meta.stability_index,
    warnings: data.meta.fhri_warnings || [],
    weights: data.meta.fhri_weights,
    subscores: data.meta.fhri_subscores
  };
}
```

## State Management (Redux/Zustand)

```javascript
// Zustand store example
import create from 'zustand';

const useFHRIStore = create((set) => ({
  fhriHistory: [],
  currentFHRI: null,
  stabilityIndex: null,

  addFHRI: (fhri) => set((state) => ({
    fhriHistory: [...state.fhriHistory, fhri].slice(-10),
    currentFHRI: fhri
  })),

  setStability: (index) => set({ stabilityIndex: index }),

  reset: () => set({
    fhriHistory: [],
    currentFHRI: null,
    stabilityIndex: null
  })
}));

// Usage in component
function ChatInterface() {
  const { fhriHistory, addFHRI, setStability } = useFHRIStore();

  const handleResponse = (response) => {
    if (response.meta?.fhri) {
      addFHRI(response.meta.fhri);
      setStability(response.meta.stability_index);
    }
  };

  // ...
}
```

## Accessibility

```jsx
function AccessibleFHRIBadge({ fhri, fhriLabel }) {
  return (
    <div
      role="status"
      aria-live="polite"
      aria-label={`Reliability score: ${fhriLabel}, ${(fhri * 100).toFixed(0)} percent`}
    >
      <span
        className="fhri-badge"
        style={{ backgroundColor: getColor(fhri) }}
      >
        {fhriLabel} ({(fhri * 100).toFixed(0)}%)
      </span>
    </div>
  );
}

function AccessibleWarnings({ warnings }) {
  if (!warnings?.length) return null;

  return (
    <div role="alert" aria-live="assertive">
      <ul className="list-disc pl-5">
        {warnings.map((warning, idx) => (
          <li key={idx}>{warning}</li>
        ))}
      </ul>
    </div>
  );
}
```

## Testing

### Unit Test (Jest/React Testing Library)

```javascript
import { render, screen } from '@testing-library/react';
import FHRIBadge from './FHRIBadge';

test('displays high reliability badge', () => {
  render(<FHRIBadge fhri={0.85} fhriLabel="High Reliability" />);

  expect(screen.getByText(/High Reliability/i)).toBeInTheDocument();
  expect(screen.getByText(/85%/i)).toBeInTheDocument();
});

test('shows warning when stability is low', () => {
  const warnings = ["Model response consistency low"];
  render(<FHRIWarnings warnings={warnings} />);

  expect(screen.getByText(/consistency low/i)).toBeInTheDocument();
});
```

## Performance Optimization

```jsx
import { memo, useMemo } from 'react';

// Memoize expensive components
const FHRIBadge = memo(({ fhri, fhriLabel, fhriHistory }) => {
  // Component implementation
});

// Memoize color calculations
const FHRIIndicator = ({ fhri, fhriLabel }) => {
  const color = useMemo(() => getColor(fhri), [fhri]);

  return (
    <span style={{ backgroundColor: color }}>
      {fhriLabel}
    </span>
  );
};
```

## Example Screenshots

### Desktop View

```
┌─────────────────────────────────────────────────────────────┐
│  What is Apple stock price?                          [Send] │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Apple (AAPL) is trading at $150.23...                      │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ [High Reliability (71%)] ▁▂▃▄▅▆▇█                    │  │
│  │ Stability: ████████████████░░░░ 82%                  │  │
│  │ Show FHRI Details ▼                                   │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Mobile View

```
┌─────────────────────┐
│ What is AAPL price? │
├─────────────────────┤
│ Apple is at $150... │
│                     │
│ ┌─────────────────┐ │
│ │ Reliability 71% │ │
│ │ Stability █░ 82%│ │
│ └─────────────────┘ │
└─────────────────────┘
```

---

## Additional Resources

- **React Sparklines**: https://github.com/borisyankov/react-sparklines
- **Chart.js** (alternative): https://www.chartjs.org/
- **Recharts** (alternative): https://recharts.org/

For questions, see [ADAPTIVE_FHRI_GUIDE.md](./ADAPTIVE_FHRI_GUIDE.md)
