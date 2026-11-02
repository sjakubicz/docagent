import { Button } from '@chakra-ui/react'
import { Upload } from 'lucide-react'
import { useRef, type ChangeEvent, type FC } from 'react'
import { FormattedMessage } from 'react-intl'
import { Tip } from '../shared/Tip'

interface UploadButtonProps {
    onFiles: (files: File[]) => Promise<void>
    loading: boolean
}

export const UploadButton: FC<UploadButtonProps> = ({ onFiles, loading }) => {
    const input = useRef<HTMLInputElement>(null)

    const onChange = async (e: ChangeEvent<HTMLInputElement>) => {
        const files = Array.from(e.target.files ?? [])
        e.target.value = ''
        if (files.length > 0) await onFiles(files)
    }

    return (
        <>
            <input
                ref={input}
                type="file"
                accept="application/pdf"
                multiple
                hidden
                onChange={onChange}
            />
            <Tip id="documents.upload.tip">
                <Button onClick={() => input.current?.click()} loading={loading}>
                    <Upload />
                    <FormattedMessage id="documents.upload" />
                </Button>
            </Tip>
        </>
    )
}
