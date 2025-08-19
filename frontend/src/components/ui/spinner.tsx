import * as React from 'react';

export const Spinner = ({ size = 'sm' }: { size?: 'sm' | 'md' | 'lg' }) => {
  const cls =
    size === 'sm'
      ? 'inline-block align-middle size-3 animate-spin text-current'
      : size === 'lg'
      ? 'inline-block align-middle size-5 animate-spin text-current'
      : 'inline-block align-middle size-4 animate-spin text-current';
  return (
    <svg role="status" aria-label="loading" className={cls} viewBox="0 0 50 50">
      <circle cx="25" cy="25" r="20" fill="none" strokeWidth="5" stroke="currentColor" strokeOpacity="0.25" />
      <path d="M45 25a20 20 0 00-20-20" fill="none" strokeWidth="5" stroke="currentColor" />
    </svg>
  );
};

export default Spinner;
