import { HStack, Stack } from '@chakra-ui/react'
import { useState, type FC } from 'react'
import { useDocuments } from '../../hooks/useDocuments'
import { ErrorAlert } from '../shared/ErrorAlert'
import { DocumentPreview } from './DocumentPreview'
import { DocumentsTable } from './DocumentsTable'
import { UploadButton } from './UploadButton'

export const DocumentsPanel: FC = () => {
    const { docs, uploading, error, upload, remove } = useDocuments()
    const [openId, setOpenId] = useState<number | null>(null)
    return (
        <Stack gap={4} pt={4}>
            <HStack>
                <UploadButton onFiles={upload} loading={uploading} />
            </HStack>
            <ErrorAlert error={error} />
            {docs.length > 0 && <DocumentsTable docs={docs} onOpen={setOpenId} onDelete={remove} />}
            {openId !== null && (
                <DocumentPreview documentId={openId} onClose={() => setOpenId(null)} />
            )}
        </Stack>
    )
}
