import { Badge, Button, IconButton, Table, Text } from '@chakra-ui/react'
import { Trash2 } from 'lucide-react'
import type { FC } from 'react'
import { FormattedDate, FormattedMessage, FormattedTime, useIntl } from 'react-intl'
import type { DocumentOut } from '../../client'
import { Tip } from '../shared/Tip'
import { StatusBadge } from './StatusBadge'

interface DocumentRowProps {
    doc: DocumentOut
    onOpen: (id: number) => void
    onDelete: (id: number) => void
}

export const DocumentRow: FC<DocumentRowProps> = ({ doc, onOpen, onDelete }) => {
    const intl = useIntl()
    return (
        <Table.Row>
            <Table.Cell>
                <Tip id="documents.open.tip">
                    <Button variant="plain" size="sm" px={0} onClick={() => onOpen(doc.id)}>
                        {doc.filename}
                    </Button>
                </Tip>
            </Table.Cell>
            <Table.Cell>
                <StatusBadge doc={doc} />
            </Table.Cell>
            <Table.Cell>
                {doc.num_pages}{' '}
                {doc.ocr_pages > 0 && (
                    <Tip id="documents.ocrPages.tip" values={{ count: doc.ocr_pages }}>
                        <Badge size="sm" colorPalette="purple">
                            <FormattedMessage
                                id="documents.ocrPages"
                                values={{ count: doc.ocr_pages }}
                            />
                        </Badge>
                    </Tip>
                )}
            </Table.Cell>
            <Table.Cell>
                <Tip id="documents.added.tip">
                    <Text as="span">
                        <FormattedDate value={doc.created_at} />{' '}
                        <FormattedTime value={doc.created_at} />
                    </Text>
                </Tip>
            </Table.Cell>
            <Table.Cell textAlign="end">
                <Tip id="documents.delete.tip" values={{ filename: doc.filename }}>
                    <IconButton
                        aria-label={intl.formatMessage(
                            { id: 'documents.delete' },
                            { filename: doc.filename },
                        )}
                        size="xs"
                        variant="ghost"
                        colorPalette="red"
                        onClick={() => onDelete(doc.id)}
                    >
                        <Trash2 />
                    </IconButton>
                </Tip>
            </Table.Cell>
        </Table.Row>
    )
}
