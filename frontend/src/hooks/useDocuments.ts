import { useEffect, useState } from 'react'
import { deleteDocument, listDocuments, uploadDocument, type DocumentOut } from '../client'

const POLL_MS = 1500

export const useDocuments = () => {
    const [docs, setDocs] = useState<DocumentOut[] | null>(null)
    const [uploading, setUploading] = useState(false)
    const [error, setError] = useState<unknown>(null)

    const refresh = async () => {
        const { data, error } = await listDocuments()
        if (error) setError(error)
        else setDocs(data ?? [])
    }

    const processing = docs?.some((d) => d.status === 'processing') ?? false
    useEffect(() => {
        if (docs !== null && !processing) return
        const timer = setTimeout(() => void refresh(), docs === null ? 0 : POLL_MS)
        return () => clearTimeout(timer)
    }, [docs, processing])

    const upload = async (files: File[]) => {
        setUploading(true)
        setError(null)
        for (const file of files) {
            const { error } = await uploadDocument({ body: { file } })
            if (error) {
                setError(error)
                break
            }
        }
        setUploading(false)
        await refresh()
    }

    const remove = async (id: number) => {
        const { error } = await deleteDocument({ path: { document_id: id } })
        if (error) setError(error)
        await refresh()
    }

    return { docs: docs ?? [], uploading, error, upload, remove }
}
