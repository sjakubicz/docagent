import { ChakraProvider, defaultSystem } from '@chakra-ui/react'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { IntlProvider } from 'react-intl'
import { App } from './App.tsx'
import { DEFAULT_LOCALE, detectLocale, MESSAGES } from './i18n'

const locale = detectLocale()

const root = document.getElementById('root')

if (!root) {
    throw new Error('Root element not found')
}

createRoot(root).render(
    <StrictMode>
        <IntlProvider locale={locale} defaultLocale={DEFAULT_LOCALE} messages={MESSAGES[locale]}>
            <ChakraProvider value={defaultSystem}>
                <App />
            </ChakraProvider>
        </IntlProvider>
    </StrictMode>,
)
