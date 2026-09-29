import type React from 'react';

export const handleRadioGroupKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
  const input = event.currentTarget;
  const options = Array.from(
    document.getElementsByName(input.name)
  ).filter((element): element is HTMLInputElement => element instanceof HTMLInputElement);

  if (event.key === ' ' || event.key === 'Enter') {
    event.preventDefault();
    input.click();
    return;
  }

  const direction = ['ArrowRight', 'ArrowDown'].includes(event.key)
    ? 1
    : ['ArrowLeft', 'ArrowUp'].includes(event.key)
      ? -1
      : 0;
  if (!direction || options.length < 2) return;

  event.preventDefault();
  const currentIndex = options.indexOf(input);
  const nextIndex = (currentIndex + direction + options.length) % options.length;
  options[nextIndex].focus();
  options[nextIndex].click();
};