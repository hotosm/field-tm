import { sum } from '../src/sum';
import { describe, expect, test } from 'vitest';

describe('Test', () => {
  test('adds 1 + 2 to equal 3', () => {
    expect(sum(1, 2)).toBe(3);
  });
});
