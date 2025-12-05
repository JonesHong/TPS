import { register, init, getLocaleFromNavigator } from 'svelte-i18n';

register('en', () => import('./locales/en.json'));
register('zh-TW', () => import('./locales/zh-TW.json'));

init({
	fallbackLocale: 'en',
	initialLocale: getLocaleFromNavigator(),
});
