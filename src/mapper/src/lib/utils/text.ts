// Utils for text manipulation

const upperDiff = '𝗔'.codePointAt(0)! - 'A'.codePointAt(0)!;
const lowerDiff = '𝗮'.codePointAt(0)! - 'a'.codePointAt(0)!;
const digitDiff = '𝟬'.codePointAt(0)! - '0'.codePointAt(0)!;

const isUpper = (n: number) => n >= 65 && n < 91;
const isLower = (n: number) => n >= 97 && n < 123;
const isDigit = (n: number) => n >= 48 && n < 58;

const bolderize = (char: string) => {
	const n = char.codePointAt(0)!;
	if (isUpper(n)) return String.fromCodePoint(n + upperDiff);
	if (isLower(n)) return String.fromCodePoint(n + lowerDiff);
	if (isDigit(n)) return String.fromCodePoint(n + digitDiff);
	return char;
};

// This function is used to convert a string from standard text to unicode bold
// text. This approach has it's downsides (consistency amongst browsers), but is
// primarily in place to get around restrictions adding bold text to translated
// strings. Translated strings cannot easily have bold text scattered throughout
// their structure, so we use unicode bold for symbols / numbers that don't
// require actual translation.
export const unicodeBold = (word: string) => [...word].map(bolderize).join('');
