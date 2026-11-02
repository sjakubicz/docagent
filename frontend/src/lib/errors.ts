export const errorMessage = (err: unknown): string => {
    if (err && typeof err === 'object' && 'detail' in err) {
        const { detail } = err as { detail: unknown }
        return typeof detail === 'string' ? detail : JSON.stringify(detail)
    }
    return err instanceof Error ? err.message : String(err)
}
