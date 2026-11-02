import { Container, Heading, HStack, Tabs } from '@chakra-ui/react'
import type { FC } from 'react'
import { FormattedMessage } from 'react-intl'
import { ChatPanel } from './components/chat/ChatPanel'
import { DocumentsPanel } from './components/documents/DocumentsPanel'
import { Tip } from './components/shared/Tip'

export const App: FC = () => (
    <Container maxW="xl" py={8}>
        <HStack justify="space-between" mb={6} align="baseline">
            <Tip id="app.title.tip">
                <Heading size="2xl">
                    <FormattedMessage id="app.title" />
                </Heading>
            </Tip>
        </HStack>

        <Tabs.Root defaultValue="chat" variant="line" lazyMount>
            <Tabs.List>
                <Tip id="app.tab.chat.tip">
                    <Tabs.Trigger value="chat">
                        <FormattedMessage id="app.tab.chat" />
                    </Tabs.Trigger>
                </Tip>
                <Tip id="app.tab.documents.tip">
                    <Tabs.Trigger value="documents">
                        <FormattedMessage id="app.tab.documents" />
                    </Tabs.Trigger>
                </Tip>
            </Tabs.List>
            <Tabs.Content value="chat">
                <ChatPanel />
            </Tabs.Content>
            <Tabs.Content value="documents">
                <DocumentsPanel />
            </Tabs.Content>
        </Tabs.Root>
    </Container>
)
