import { CloseButton, Drawer, Portal, Tabs } from '@chakra-ui/react'
import type { FC } from 'react'
import { FormattedMessage } from 'react-intl'
import { useDocument } from '../../hooks/useDocument'
import { ErrorAlert } from '../shared/ErrorAlert'
import { Tip } from '../shared/Tip'
import { PageList } from './PageList'
import { PdfFrame } from './PdfFrame'

interface DocumentPreviewProps {
    documentId: number
    onClose: () => void
}

export const DocumentPreview: FC<DocumentPreviewProps> = ({ documentId, onClose }) => {
    const { doc, error } = useDocument(documentId)
    const hasFile = doc?.has_file ?? false
    return (
        <Drawer.Root open size="xl" onOpenChange={(e) => !e.open && onClose()}>
            <Portal>
                <Drawer.Backdrop />
                <Drawer.Positioner>
                    <Drawer.Content>
                        <Drawer.Header>
                            <Drawer.Title>{doc?.filename}</Drawer.Title>
                        </Drawer.Header>
                        <Drawer.Body display="flex" flexDirection="column">
                            <ErrorAlert error={error} />
                            {doc && (
                                <Tabs.Root
                                    defaultValue={hasFile ? 'pdf' : 'text'}
                                    lazyMount
                                    flex="1"
                                    display="flex"
                                    flexDirection="column"
                                >
                                    <Tabs.List>
                                        <Tip
                                            id={
                                                hasFile
                                                    ? 'preview.tab.pdf.tip'
                                                    : 'preview.tab.pdf.missing.tip'
                                            }
                                        >
                                            <Tabs.Trigger value="pdf" disabled={!hasFile}>
                                                <FormattedMessage id="preview.tab.pdf" />
                                            </Tabs.Trigger>
                                        </Tip>
                                        <Tip id="preview.tab.text.tip">
                                            <Tabs.Trigger value="text">
                                                <FormattedMessage id="preview.tab.text" />
                                            </Tabs.Trigger>
                                        </Tip>
                                    </Tabs.List>
                                    <Tabs.Content value="pdf" flex="1">
                                        <PdfFrame document={doc} />
                                    </Tabs.Content>
                                    <Tabs.Content value="text">
                                        <PageList pages={doc.pages} />
                                    </Tabs.Content>
                                </Tabs.Root>
                            )}
                        </Drawer.Body>
                        <Tip id="preview.close.tip">
                            <Drawer.CloseTrigger asChild>
                                <CloseButton size="sm" />
                            </Drawer.CloseTrigger>
                        </Tip>
                    </Drawer.Content>
                </Drawer.Positioner>
            </Portal>
        </Drawer.Root>
    )
}
