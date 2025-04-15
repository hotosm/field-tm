// uno.config.ts
import { defineConfig, transformerDirectives } from 'unocss';

export default defineConfig({
	transformers: [transformerDirectives()],
});
