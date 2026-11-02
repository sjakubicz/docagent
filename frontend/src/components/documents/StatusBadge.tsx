import { Badge, Spinner } from '@chakra-ui/react'
import type { FC } from 'react'
import { FormattedMessage } from 'react-intl'
import type { DocumentOut } from '../../client'
import { Tip } from '../shared/Tip'

const PALETTE: Record<DocumentOut['status'], string> = {
    processing: 'blue',
    ready: 'green',
    failed: 'red',
}

interface StatusBadgeProps {
    doc: DocumentOut
}

export const StatusBadge: FC<StatusBadgeProps> = ({ doc }) => (
    <Tip id={`documents.status.${doc.status}.tip`} values={{ error: doc.error ?? '' }}>
        <Badge size="sm" colorPalette={PALETTE[doc.status]}>
            {doc.status === 'processing' && <Spinner size="xs" />}
            <FormattedMessage id={`documents.status.${doc.status}`} />
        </Badge>
    </Tip>
)
