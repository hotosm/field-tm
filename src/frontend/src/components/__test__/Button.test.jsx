import { describe, expect, test } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import Button from '../common/Button';
import { useState } from 'react';

describe('Button', () => {
  test('renders', () => {
    render(<Button btnText="NEXT" />);
    expect(screen.getByText('NEXT')).toBeDefined();
  });
  /**
   * Test suite for the Button component
   */
  describe('Button', () => {
    /**
     * Test to verify that the Button component renders with the correct text
     */
    test('renders', () => {
      render(<Button btnText="NEXT" />);
      expect(screen.getByText('NEXT')).toBeDefined();
    });

    /**
     * Test to verify that the count increases when the button is clicked
     */
    test('should increase count by 1', () => {
      // Arrange
      const ButtonWithCount = () => {
        const [count, setCount] = useState(0);
        return (
          <>
            <div data-testid="count">{count}</div>

            <Button btnText="Click" onClick={() => setCount(count + 1)} />
          </>
        );
      };

      // Act
      render(<ButtonWithCount />);

      const count = screen.getByTestId('count');
      const button = screen.getByText('Click');

      fireEvent.click(button);

      // Assert
      expect(count.textContent).toBe('1');
    });

    /**
     * Test to verify that the Button component renders a count element if provided
     */
    it('should render a count element if provided', () => {
      render(<Button btnText="Test Button" count={5} />);
      expect(screen.getByText('5')).toBeInTheDocument();
    });

    /**
     * Test to verify the styling of the Button component based on the btnType prop
     */
    it("should render a button with a red border and text if btnType prop is 'other'", () => {
      render(<Button btnText="Test Button" btnType="other" />);
      expect(screen.getByTestId('test-button')).toHaveClass(
        'fmtm-py-1 fmtm-px-4 fmtm-text-red-600 fmtm-rounded-lg fmtm-border-[1px] fmtm-border-red-600 hover:fmtm-text-red-700 hover:fmtm-border-red-700',
      );
    });
  });
});
