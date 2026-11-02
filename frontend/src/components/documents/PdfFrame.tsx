import { chakra } from '@chakra-ui/react'
import type { FC } from 'react'
import { useIntl } from 'react-intl'
import type { DocumentDetail } from '../../client'
import { documentFileUrl } from '../../lib/documents'

interface PdfFrameProps {
    document: DocumentDetail
}

export const PdfFrame: FC<PdfFrameProps> = ({ document }) => {
    const intl = useIntl()
    return (
        <chakra.iframe
            src={documentFileUrl(document.id)}
            title={intl.formatMessage(
                { id: 'preview.frame.title' },
                { filename: document.filename },
            )}
            width="100%"
            height="100%"
            minH="70vh"
            borderWidth="1px"
            borderRadius="md"
        />
    )
}
