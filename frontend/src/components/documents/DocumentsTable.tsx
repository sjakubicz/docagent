import { Table } from '@chakra-ui/react'
import type { FC } from 'react'
import { FormattedMessage } from 'react-intl'
import type { DocumentOut } from '../../client'
import type { MessageId } from '../../i18n'
import { Tip } from '../shared/Tip'
import { DocumentRow } from './DocumentRow'

const COLUMNS: { label: MessageId; tip: MessageId }[] = [
    { label: 'documents.column.file', tip: 'documents.column.file.tip' },
    { label: 'documents.column.status', tip: 'documents.column.status.tip' },
    { label: 'documents.column.pages', tip: 'documents.column.pages.tip' },
    { label: 'documents.column.added', tip: 'documents.column.added.tip' },
]

interface DocumentsTableProps {
    docs: DocumentOut[]
    onOpen: (id: number) => void
    onDelete: (id: number) => void
}

export const DocumentsTable: FC<DocumentsTableProps> = ({ docs, onOpen, onDelete }) => (
    <Table.Root size="sm">
        <Table.Header>
            <Table.Row>
                {COLUMNS.map(({ label, tip }) => (
                    <Tip key={label} id={tip}>
                        <Table.ColumnHeader>
                            <FormattedMessage id={label} />
                        </Table.ColumnHeader>
                    </Tip>
                ))}
                <Table.ColumnHeader />
            </Table.Row>
        </Table.Header>
        <Table.Body>
            {docs.map((doc) => (
                <DocumentRow key={doc.id} doc={doc} onOpen={onOpen} onDelete={onDelete} />
            ))}
        </Table.Body>
    </Table.Root>
)
