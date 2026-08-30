import { useEffect } from 'react'
import Button from './Button'

function ConfirmDialog({
  title,
  message,
  confirmLabel = 'Delete',
  cancelLabel = 'Cancel',
  isConfirming = false,
  onConfirm,
  onCancel,
}) {
  useEffect(() => {
    function onKeyDown(event) {
      if (event.key === 'Escape' && !isConfirming) {
        onCancel()
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [isConfirming, onCancel])

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-ink/40 px-4">
      <div
        className="w-full max-w-md rounded-lg border border-line bg-surface p-6 shadow-lg"
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-dialog-title"
      >
        <h2 id="confirm-dialog-title" className="font-display text-lg font-semibold text-ink">
          {title}
        </h2>
        <p className="mt-3 text-muted">{message}</p>
        <div className="mt-6 flex justify-end gap-3">
          <Button variant="secondary" type="button" onClick={onCancel} disabled={isConfirming}>
            {cancelLabel}
          </Button>
          <Button variant="danger" type="button" onClick={onConfirm} disabled={isConfirming}>
            {isConfirming ? 'Deleting…' : confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  )
}

export default ConfirmDialog
