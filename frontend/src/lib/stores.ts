import { writable } from 'svelte/store';
import type { TranslationItem } from './types';

export const selectedTranslation = writable<TranslationItem | null>(null);
