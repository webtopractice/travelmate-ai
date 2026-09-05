/**
 * Shared lightweight markdown-ish renderer — bold (**text**) + line breaks.
 * Used by MessageBubble and the result cards so formatting stays consistent.
 */

import React from 'react';

export function renderFormattedText(content) {
  if (!content) return null;

  const lines = content.split('\n');

  return lines.map((line, i) => {
    const parts = line.split(/(\*\*.*?\*\*)/g);
    const rendered = parts.map((part, j) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={j}>{part.slice(2, -2)}</strong>;
      }
      return part;
    });

    return (
      <React.Fragment key={i}>
        {rendered}
        {i < lines.length - 1 && <br />}
      </React.Fragment>
    );
  });
}
